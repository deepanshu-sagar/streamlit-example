import streamlit as st
import openai, re

openai.api_key = ''

cuisines_by_ethnicity = {
    "American": ["Fast Food", "Comfort Food", "BBQ", "Cajun", "Soul Food", "Tex-Mex", "New England"],
    "Chinese": ["Szechuan", "Cantonese", "Hunan", "Shandong", "Fujian", "Zhejiang", "Jiangsu"],
    "Indian": ["North Indian", "South Indian", "West Indian", "East Indian", "Rajasthani", "Punjabi", "Goan"],
    "Italian": ["Tuscan", "Sicilian", "Lazio", "Veneto", "Lombard", "Piedmontese", "Calabrian"],
    "Mexican": ["Oaxacan", "Veracruz", "Yucatecan", "Poblano", "Norteno", "Jalisco", "Baja"],
    "Japanese": ["Kanto", "Kansai", "Hokkaido", "Kyushu", "Chugoku", "Tohoku", "Chubu"],
    "Thai": ["Central Thai", "Isan", "Southern Thai", "Northern Thai", "Western Thai", "Eastern Thai", "Bangkok"]
}

def suggest_ingredients(cuisine):
    prompt = f"What are some typical ingredients used in {cuisine} cuisine? only ingriedients names. in comma separated format"
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

def generate_recipe(ingredients, cuisine):
    prompt = f"Create a {cuisine} recipe using the following ingredients: {ingredients} in the style of tarla dalal and sanjeev kapoor."
    completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"{prompt}"}
  ]
)
    return completion.choices[0].message

st.title("Ethnicity Based Recipe Generator")

if "ethnicity" not in st.session_state:
    st.session_state["ethnicity"] = list(cuisines_by_ethnicity.keys())[0]

if "cuisine" not in st.session_state:
    st.session_state["cuisine"] = cuisines_by_ethnicity[st.session_state["ethnicity"]][0]

if "ingredients" not in st.session_state:
    st.session_state["ingredients"] = suggest_ingredients(st.session_state["cuisine"])

if "previous_cuisine" not in st.session_state:
    st.session_state["previous_cuisine"] = st.session_state["cuisine"]

ethnicity = st.selectbox('Select Ethnicity', list(cuisines_by_ethnicity.keys()), key="ethnicity")
cuisine = st.selectbox('Select Cuisine', cuisines_by_ethnicity[ethnicity], key="cuisine")

# Check if cuisine has changed, if so, update ingredients
if st.session_state["previous_cuisine"] != st.session_state["cuisine"]:
    st.session_state["ingredients"] = suggest_ingredients(st.session_state["cuisine"])
    st.session_state["previous_cuisine"] = st.session_state["cuisine"]

ingredients = st.text_area("Ingredients (comma-separated)", st.session_state["ingredients"], key="ingredients")

if st.button('Generate Recipes'):
    for i in range(3):
        recipe = generate_recipe(ingredients, cuisine)
        recipe_content = recipe["content"]
        recipe_content = recipe_content.replace("\n", "<br />")
        st.markdown(f'<div style="height: 600px; overflow-y: auto;">{recipe_content}</div>', unsafe_allow_html=True)
