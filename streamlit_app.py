import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import udf
from snowflake.snowpark.types import IntegerType

# --------------------------------------
# SNOWFLAKE CONNECTION USING st.connection
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
    my_dataframe = session.table("smoothies.public.fruit_options")
except Exception as e:
    st.error(f"Error loading fruit_options: {e}")
    my_dataframe = None

if my_dataframe is not None:
    st.subheader("Available Fruits")
    st.dataframe(my_dataframe)

import requests
smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
st.text(smoothiefroot_response)
# st.text(smoothiefroot_response.json())
sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)


# --------------------------------------
# SMOOTHIE FORM
# --------------------------------------
with st.form("smoothie_form"):
    try:
        options = (
            my_dataframe.select("FRUIT_NAME").to_pandas()["FRUIT_NAME"].tolist()
        )
    except Exception:
        options = ["Apples", "Oranges"]

    ingredients = st.multiselect("Choose up to 5:", options, max_selections=5)
    name = st.text_input("Your Name")
    submit = st.form_submit_button("Submit Order")

# --------------------------------------
# INSERT ORDER SAFELY
# --------------------------------------
if submit:
    if not ingredients:
        st.warning("Please select at least one ingredient.")
    elif not name:
        st.warning("Please enter your name.")
    else:
        try:
            session.table("smoothies.public.orders").insert({
                "INGREDIENTS": ", ".join(ingredients),
                "NAME_ON_ORDER": name
            })
            st.success(f"Order placed, {name}! 🎉")
        except Exception as e:
            st.error(f"Error placing order: {e}")
# -----------------------------------------------------
# NUTRITION API (YOUR REQUESTS CODE DIRECTLY HERE)
# -----------------------------------------------------
        st.subheader("Nutrition Information")

        for fruit_chosen in ingredients_list:

            st.markdown(f"### {fruit_chosen}")

            try:
                response = requests.get(
                    f"https://my.smoothiefroot.com/api/fruit/{fruit_chosen}"
                )

                if response.status_code == 200:
                    st.dataframe(
                        data=response.json(),
                        use_container_width=True
                    )
                else:
                    st.error(f"Could not fetch nutrition info for {fruit_chosen}")

            except Exception as e:
                st.error(f"API error for {fruit_chosen}: {e}")
