import streamlit as st
import requests
from snowflake.snowpark import Session
from snowflake.snowpark.functions import udf
from snowflake.snowpark.types import IntegerType

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
    # Select both FRUIT_NAME and SEARCH_ON columns
    my_dataframe = session.table("smoothies.public.fruit_options").select("FRUIT_NAME", "SEARCH_ON")
    df_pandas = my_dataframe.to_pandas()
    # Extract lists of fruit names and search terms
    fruit_names = df_pandas["FRUIT_NAME"].tolist()
    search_terms = df_pandas["SEARCH_ON"].tolist()
except Exception as e:
    st.error(f"Error loading fruit_options: {e}")
    fruit_names = ["Apples", "Oranges"]  # fallback lists
    search_terms = ["Apples", "Oranges"]
    my_dataframe = None

if my_dataframe is not None:
    st.subheader("Available Fruits")
    st.dataframe(my_dataframe)

# --------------------------------------
# SMOOTHIE FORM
# --------------------------------------
with st.form("smoothie_form"):
    # Use fruit_names for multiselect display
    ingredients = st.multiselect("Choose up to 5:", fruit_names, max_selections=5)
    name = st.text_input("Your Name")
    submit = st.form_submit_button("Submit Order")

# --------------------------------------
# HANDLE FORM SUBMISSION
# --------------------------------------
if submit:
    if not ingredients:
        st.warning("Please select at least one ingredient.")
        st.stop()
    if not name:
        st.warning("Please enter your name.")
        st.stop()

    # Insert order into Snowflake table
    try:
        session.table("smoothies.public.orders").insert({
            "INGREDIENTS": ", ".join(ingredients),
            "NAME_ON_ORDER": name
        })
        st.success(f"Order placed, {name}! 🎉")
    except Exception as e:
        st.error(f"Error placing order: {e}")
        st.stop()

    # Map selected fruits to SEARCH_ON terms
    search_term_map = dict(zip(fruit_names, search_terms))
    selected_search_terms = [search_term_map[fruit] for fruit in ingredients]

    # Show nutrition information for each selected fruit using SEARCH_ON term
    st.subheader("Nutrition Information")

    for term in selected_search_terms:
        # Display the search value info
        search_on = df_pandas.loc[df_pandas['SEARCH_ON'] == term, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {term} is {search_on}.")

        st.markdown(f"### {term}")

        try:
            response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{term}")

            if response.status_code == 200:
                st.dataframe(
                    data=response.json(),
                    use_container_width=True
                )
            else:
                st.error(f"Could not fetch nutrition info for {term}")

        except Exception as e:
            st.error(f"API error for {term}: {e}")
