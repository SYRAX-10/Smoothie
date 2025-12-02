import streamlit as st
import requests
from snowflake.snowpark import Session
import hashlib
import json

# --------------------------------------
# SNOWFLAKE CONNECTION
# --------------------------------------
connection_parameters = st.secrets["connections"]["snowflake"]
session = Session.builder.configs(connection_parameters).create()

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
    fruit_names = []
    df_pandas = None

st.subheader("Available Fruits")
st.dataframe(df_pandas)

# --------------------------------------
# SMOOTHIE FORM
# --------------------------------------
with st.form("smoothie_form"):
    ingredients_list = st.multiselect("Choose up to 5:", fruit_names, max_selections=5)
    name = st.text_input("Your Name")
    submit = st.form_submit_button("Submit Order")

# --------------------------------------
# CLEAN + HASH LOGIC
# --------------------------------------
def normalize_ingredients(ingredient_array):
    """Remove extra spaces and format consistently."""
    cleaned = [i.strip() for i in ingredient_array]
    return cleaned

def generate_hash(ingredient_array):
    """Stable hash using SHA-256 instead of Python random hash()."""
    cleaned = normalize_ingredients(ingredient_array)
    joined = ",".join(cleaned)          # NO SPACES
    encoded = joined.encode("utf-8")
    return int(hashlib.sha256(encoded).hexdigest(), 16) % (2**63)

# --------------------------------------
# HANDLE FORM SUBMISSION
# --------------------------------------
if submit:

    if not ingredients_list:
        st.warning("Select at least one ingredient.")
        st.stop()

    if not name:
        st.warning("Enter your name.")
        st.stop()

    # Clean ingredient list
    cleaned_ings = normalize_ingredients(ingredients_list)
    ingredient_string = ", ".join(cleaned_ings)

    # Generate stable hash
    hash_value = generate_hash(cleaned_ings)

    # Insert into Snowflake safely
    try:
        session.table("smoothies.public.orders").insert_row(
            {"INGREDIENTS": ingredient_string, "NAME_ON_ORDER": name, "HASH_ING": hash_value}
        )
        st.success(f"Order placed, {name}! 🎉")
        st.info(f"Hash Value Stored: {hash_value}")
    except Exception as e:
        st.error(f"Error placing order: {e}")
        st.stop()

    # --------------------------------------
    # Nutrition Info
    # --------------------------------------
    st.subheader("Nutrition Information")

    for fruit_chosen in cleaned_ings:

        # Correct SEARCH_ON lookup
        row = df_pandas.loc[df_pandas['FRUIT_NAME'] == fruit_chosen]

        if row.empty:
            st.error(f"No SEARCH_ON value found for {fruit_chosen}")
            continue

        search_on = row['SEARCH_ON'].iloc[0]
        st.write(f"API lookup value for **{fruit_chosen}** → `{search_on}`")

        # Call API
        try:
            api_url = f"https://my.smoothiefroot.com/api/fruit/{search_on}"
            response = requests.get(api_url)

            if response.status_code == 200:
                st.dataframe(response.json())
            else:
                st.error(f"API returned an error for {fruit_chosen}")
        except Exception as e:
            st.error(f"API error for {fruit_chosen}: {e}")
