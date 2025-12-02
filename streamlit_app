# Import python packages
import streamlit as st

# NOTE: The 'Session' class is implicitly used by get_active_session.
# No need for 'from snowflake.snowpark import Session' if only using get_active_session().

# Get the active Snowpark session

cnx = st.connection("snowflake")
session = cnx.session()


# --- App Title and Setup ---
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom smoothie, and name your order!
    """
)

# Define the Snowpark DataFrame by querying the fruit options table
try:
    my_dataframe = session.table("smoothies.public.fruit_options")
except Exception as e:
    st.error(f"Error connecting to or querying the 'fruit_options' table: {e}")
    my_dataframe = None

# Display the full Snowpark DataFrame for reference
if my_dataframe is not None:
    st.header("Available Fruits (from Snowflake Table):")
    st.dataframe(data=my_dataframe, use_container_width=True)

# --- Start of the Streamlit Form (Critical for Submission Control) ---
with st.form(key='my_smoothie_form'):
    
    # 1. Fetch Data for Multiselect Widget Options (Snowpark to Python list conversion)
    options_list = []
    try:
        if my_dataframe is not None:
            # Fetch the 'FRUIT_NAME' column, convert results to Pandas, and extract as a list
            options_list = my_dataframe.select("FRUIT_NAME").to_pandas()["FRUIT_NAME"].tolist()
        
        if not options_list:
             options_list = ['Apples', 'Oranges'] # Fallback
            
    except Exception as e:
        st.error(f"Error fetching data for multiselect: {e}")
        options_list = ['Error Loading Data']

    # 2. Multiselect Widget
    ingredients_list = st.multiselect(
        'Choose up to 5 ingredients:',
        options_list,
        max_selections = 5
    )

    # 3. Text Input Widget for Name on Order
    name_on_order = st.text_input('Name on Smoothie:')
    
    # 4. Submit Button
    submit_button = st.form_submit_button('SUBMIT ORDER')

# --- SUBMISSION LOGIC executed ONLY when Submit Button is Clicked ---
if submit_button:
    
    # Validation Check 1: Must select ingredients
    if not ingredients_list:
        st.warning("⚠️ Please select at least one ingredient before submitting.")
        st.stop()
        
    # Validation Check 2: Must enter a name
    if not name_on_order:
        st.warning("⚠️ Please enter a name for your smoothie before submitting.")
        st.stop()
        
    # --- PROCESSING AND SAVING ---

    # 1. Format the list of ingredients into a single, comma-separated string (cleaner than the loop)
    ingredients_string = ', '.join(ingredients_list)
    
    # 2. Define the SQL command to insert the order
    # NOTE: The SQL now correctly includes both the INGREDIENTS and NAME_ON_ORDER columns.
    # We use f-strings for simplicity, but beware of SQL injection risks in production.
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (INGREDIENTS, NAME_ON_ORDER)
        VALUES ('{ingredients_string}', '{name_on_order}');
    """
    
    # 3. Execute the command using Snowpark
    try:
        session.sql(my_insert_stmt).collect()
        
        # Display success feedback
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        st.balloons()
        
        # Display the final order details
        st.subheader("Order Details:")
        st.markdown(f"**Name:** `{name_on_order}`")
        st.markdown(f"**Ingredients:** `{ingredients_string}`")
        
    except Exception as e:
        st.error(f"Database Error: Could not save order to database. Error: {e}")



