# streamlit_app.py

import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import udf

# ------------------------------
# Snowflake Connection (LOCAL / GITHUB / STREAMLIT CLOUD)
# ------------------------------

session = get_active_session()
# ------------------------------
# UDF Example
# ------------------------------
@udf(session=session)
def myfunc(x: int) -> int:
    return x + 1

# ------------------------------
# STREAMLIT UI
# ------------------------------

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your smoothie!")

# Load fruit table
try:
    my_dataframe = session.table("smoothies.public.fruit_options")
except Exception as e:
    st.error(f"Error loading fruit_options: {e}")
    my_dataframe = None

if my_dataframe is not None:
    st.subheader("Available Fruits")
    st.dataframe(my_dataframe)

with st.form("smoothie_form"):
    try:
        options = my_dataframe.select("FRUIT_NAME").to_pandas()["FRUIT_NAME"].tolist()
    except:
        options = ["Apples", "Oranges"]

    ingredients = st.multiselect("Choose up to 5:", options, max_selections=5)
    name = st.text_input("Your Name")
    submit = st.form_submit_button("Submit Order")

if submit:
    if not ingredients:
        st.warning("Select at least one ingredient.")
    elif not name:
        st.warning("Enter a name.")
    else:
        ingredients_str = ", ".join(ingredients)
        insert_sql = f"""
            INSERT INTO smoothies.public.orders (INGREDIENTS, NAME_ON_ORDER)
            VALUES ('{ingredients_str}', '{name}');
        """
        try:
            session.sql(insert_sql).collect()
            st.success(f"Order placed, {name}! 🎉")
        except Exception as e:
            st.error(f"Database error: {e}")
