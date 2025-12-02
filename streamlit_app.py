import streamlit as st
import requests
from snowflake.snowpark import Session
from snowflake.snowpark.functions import udf
from snowflake.snowpark.types import IntegerType
import re  # for regex string normalization

# --------------------------------------
# SNOWFLAKE CONNECTION
# --------------------------------------
connection_parameters = st.secrets["connections"]["snowflake"]
session = Session.builder.configs(connection_parameters).create()

# --------------------------------------
# UDF EXAMPLE (SAFE)
# --------------------------------------
@udf(return_type=IntegerType(), input_types=[IntegerType()], session=session)
def myfunc(x):
    return x + 1

# --------------------------------------
# STREAMLIT UI
# --------------------------------------
st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your smoothie!")

# --------------------------------------
# LOAD FRUIT TABLE
# --------------------------------------
try:
    my_dataframe = session.table("smoothies.public.fruit_options").select("FRUIT_NAME", "SEARCH_ON")
    df_pandas = my_dataframe.to_pandas()
    fruit_names = df_pandas["FRUIT_NAME"].tolist()
except Exception as e:
    st.error(f"Error loading fruit_options: {e}")
    fruit_names = ["Apples", "Oranges"]
    df_pandas = None

if my_dataframe is not None:
    st.subheader("Available Fruits")
    st.dataframe(my_dataframe)

# --------------------------------------
# SMOOTHIE FORM
# --------------------------------------
with st.form("smoothie_form"):
    ingredients_list = st.multiselect("Choose up to 5:", fruit_names, max_selections=5)
    name = st.text_input("Your Name")
    submit = st.form_submit_button("Submit Order")

# --------------------------------------
# HANDLE FORM SUBMISSION
# --------------------------------------
if submit:
    if not ingredients_list:
        st.warning("Please select at least one ingredient.")
        st.stop()
    if not name:
        st.warning("Please enter your name.")
        st.stop()

    # Normalize ingredients string for consistent spacing and hashing
    # Strip extra spaces from each fruit, join with ", " exactly one space after comma
    ingredients_str = ", ".join([fruit.strip() for fruit in ingredients_list])
    # Regex to remove extra spaces around commas if any (just a safeguard)
    ingredients_str = re.sub(r'\s*,\s*', ', ', ingredients_str.strip())

    # Insert order into Snowflake table using normalized string
    try:
        insert_stmt = f"""
            INSERT INTO smoothies.public.orders (INGREDIENTS, NAME_ON_ORDER)
            VALUES ('{ingredients_str}', '{name}')
        """
        session.sql(insert_stmt).collect()
        st.success(f"Order placed, {name}! 🎉")
    except Exception as e:
        st.error(f"Error placing order: {e}")
        st.stop()

    # --------------------------------------
    # Show nutrition info for each selected fruit
    # --------------------------------------
    st.subheader("Nutrition Information")

    for fruit_chosen in ingredients_list:
        # Get SEARCH_ON value from pandas dataframe safely
        search_on = df_pandas.loc[df_pandas['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}.")

        st.subheader(f"{fruit_chosen} Nutrition Information")

        try:
            smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")

            if smoothiefroot_response.status_code == 200:
                st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
            else:
                st.error(f"Could not fetch nutrition info for {fruit_chosen}")

        except Exception as e:
            st.error(f"API error for {fruit_chosen}: {e}")


