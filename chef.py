import streamlit as st
import openai, re,os

openai.api_key = os.getenv("OPENAI_API_KEY")

cuisines_by_ethnicity = {
    "American": ["Fast Food", "Comfort Food", "BBQ", "Cajun", "Soul Food", "Tex-Mex", "New England"],
    "Chinese": ["Szechuan", "Cantonese", "Hunan", "Shandong", "Fujian", "Zhejiang", "Jiangsu"],
    "Indian": ["North Indian", "South Indian", "West Indian", "East Indian", "Rajasthani", "Punjabi", "Goan"],
    "Italian": ["Tuscan", "Sicilian", "Lazio", "Veneto", "Lombard", "Piedmontese", "Calabrian"],
    "Mexican": ["Oaxacan", "Veracruz", "Yucatecan", "Poblano", "Norteno", "Jalisco", "Baja"],
    "Japanese": ["Kanto", "Kansai", "Hokkaido", "Kyushu", "Chugoku", "Tohoku", "Chubu"],
    "Thai": ["Central Thai", "Isan", "Southern Thai", "Northern Thai", "Western Thai", "Eastern Thai", "Bangkok"]
}



def suggest_ingredients(cuisine,vegnonveg):
    prompt = f"What are some typical ingredients used in {cuisine} cuisine for {vegnonveg} person? only ingriedients names. in comma separated format. in the style of tarla dalal and sanjeev kapoor. Example : Onion, Lettuce, Carrot"
    completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"{prompt}"}
  ]
)
    #print (completion.choices[0].message["content"])
    #ing = re.findall("- (.*)", completion.choices[0].message['content'])
    #print (ing)
    return completion.choices[0].message["content"]

def generate_recipe(ingredients, cuisine,vegnonveg):
    prompt = f"Create a {cuisine} recipe for {vegnonveg} person using the following ingredients: {ingredients} in the style of tarla dalal and sanjeev kapoor."
    completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"{prompt}"}
  ]
)
    return completion.choices[0].message

st.title("Ethnicity Based Recipe Generator")

vegnonveg = st.selectbox('Select Veg/ Non-Veg', ["Veg", "Non-Veg"], key="vegnonveg")

# Initialize session state if not already initialized
if "ethnicity" not in st.session_state:
    st.session_state["ethnicity"] = list(cuisines_by_ethnicity.keys())[0]

if "cuisine" not in st.session_state:
    st.session_state["cuisine"] = cuisines_by_ethnicity[st.session_state["ethnicity"]][0]

if "previous_cuisine" not in st.session_state:
    st.session_state["previous_cuisine"] = ""

if "ingredients" not in st.session_state:
    st.session_state["ingredients"] = ""

ethnicity = st.selectbox('Select Ethnicity', list(cuisines_by_ethnicity.keys()), key="ethnicity")
cuisine = st.selectbox('Select Cuisine', cuisines_by_ethnicity[ethnicity], key="cuisine")

# Populate Ingredients Button
if st.button('Populate Ingredients'):
    # Check if cuisine has changed, if so, update ingredients
    if st.session_state["previous_cuisine"] != st.session_state["cuisine"]:
        st.session_state["ingredients"] = suggest_ingredients(st.session_state["cuisine"], vegnonveg)
        st.session_state["previous_cuisine"] = st.session_state["cuisine"]

# If ingredients are available, show the text area
if st.session_state["ingredients"]:
    ingredients = st.text_area("Ingredients (comma-separated)", st.session_state["ingredients"], key="ingredients")

    if st.button('Generate Recipes'):
        recipe = generate_recipe(ingredients, cuisine, vegnonveg)
        recipe_content = recipe["content"]
        recipe_content = recipe_content.replace("\n", "<br />")
        st.markdown(f'''
            <div style="height: 600px; overflow-y: auto; border: 2px solid #000; padding: 10px;">
                {recipe_content}
            </div>
        ''', unsafe_allow_html=True)

st.title("Diet Plan Generator")

def generate_diet_plan(goals):
    """Generate a diet plan based on goals using OpenAI."""
    
    if not goals:
        return "Please select at least one goal to get a diet plan."

    prompt = f"Please provide a diet plan for the following goals: {' and '.join(goals)}. Break it down into Breakfast, Lunch, and Dinner."

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a knowledgeable nutritionist."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return completion.choices[0].message["content"]

# Initialize session state variables if not already present
if 'submitted_details' not in st.session_state:
    st.session_state.submitted_details = False
if 'bmi' not in st.session_state:
    st.session_state.bmi = None
if 'category' not in st.session_state:
    st.session_state.category = None
if 'name' not in st.session_state:
    st.session_state.name = ""

# Details input container
details_container = st.container()
with details_container:
    if not st.session_state.submitted_details:
        st.session_state.name = st.text_input("Name:")
        age = st.number_input("Age:", min_value=1, max_value=120)
        height = st.number_input("Height (in cm):", min_value=50.0, max_value=250.0)
        weight = st.number_input("Weight (in kg):", min_value=1.0, max_value=200.0)

        if st.button('Submit Details'):
            st.session_state.submitted_details = True
            height_m = height / 100.0
            st.session_state.bmi = weight / (height_m ** 2)

            # Determine BMI Category
            if st.session_state.bmi < 18.5:
                st.session_state.category = "Underweight"
            elif 18.5 <= st.session_state.bmi < 24.9:
                st.session_state.category = "Normal weight"
            elif 25 <= st.session_state.bmi < 29.9:
                st.session_state.category = "Overweight"
            else:
                st.session_state.category = "Obesity"

# Goals input container
goals_container = st.container()
with goals_container:
    if st.session_state.submitted_details:
        st.write(f"Hello {st.session_state.name}, your BMI is {st.session_state.bmi:.2f} which falls under the '{st.session_state.category}' category.")

        goals = st.multiselect(
            "Select your diet goals:",
            ["Weight loss", "Weight gain", "Fat loss", "Immunity Boosting", "Generate Stamina"]
        )

        if st.button('Generate Diet Plan'):
            if goals:
                diet_plan = generate_diet_plan(goals)
                st.markdown(diet_plan)
            else:
                st.write("Please select at least one goal to get a diet plan.")