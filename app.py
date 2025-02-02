import streamlit as st
from dotenv import load_dotenv
from langfuse.decorators import observe
from langfuse.openai import OpenAI
from pydantic import BaseModel
import streamlit.components.v1 as components
import os
import time


st.set_page_config(page_title="IAD", layout="centered", menu_items={'About': 'IAD by JK'})
st.title("Inteligentny Asystent Decyzyjny")

class ResponseModel(BaseModel):
    summary: str
    options: list[str]

MODEL = "gpt-4o-mini"
session_token_limit = 25_000
session_token_limit_and_report = 27_000

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_token_limit():
    if st.session_state['total_tokens_used'] >= session_token_limit:
        st.error("Limit tokenów został osiągnięty.")
        st.success("Możesz jeszcze wygenerować raport. Naciśnij Generuj Raport.")
        st.session_state["buttons_status"] = True
        time.sleep(2)
        return st.session_state["buttons_status"]
    else:
        st.session_state["buttons_status"] = False
        return st.session_state["buttons_status"]

def check_token_limit_for_report():
    if st.session_state['total_tokens_used'] >= session_token_limit_and_report:
        st.error("Limit tokenów został osiągnięty. Aplikacja została zatrzymana.")
        st.stop()

@observe(name="iad-steps") 
def generate_next_steps(text, previous_step=""):
    check_token_limit()
    check_token_limit_for_report()
    messages = [
        {
            'role': 'system',
            'content': f"""
            Jesteś asystentem, który pomaga podejmować decyzje. 
            Przedstaw od 2 do 4 opcji rozwiązania problemu, jako punkty: 1. , 2. itp. 
            W załączeniu masz opisany problem i wcześniej wybrane opcje. Użytkownik poda tobie wybraną opcję, którą rozwiń w tej odpowiedzi. 
            Nie wracaj do poprzednich, niewybranych opcji.
            Jeśli nie ma wcześniej wybranej opcji, to od razu przedstaw rozwiązania z uzasadnieniem.
            Twoja odpowiedź musi rozpoczynać się krótkim podsumowaniem problemu użytkownika, a następnie zawierać porady w punktach. 
            Nie dodawaj żadnych komentarzy ani próśb na końcu odpowiedzi.
            Przykład odpowiedzi: 
            Opisowe podsumowanie problemu.
            1. Opis pierwszej porady.
            2. Opis drugiej porady. 
            
            Poprzednia odpowiedź: {previous_step}
            """,
        },
        {"role": "user", "content": text}
    ]
    response = openai_client.beta.chat.completions.parse(
        model=MODEL,
        response_format=ResponseModel,
        messages=messages,
        temperature=0,
    )
    usage = response.usage.total_tokens
    st.session_state['total_tokens_used'] += usage
    return {"content": response}

@observe(name="iad-report") 
def generate_report(problem, steps, options):
    check_token_limit_for_report()
    messages = [
        {
            'role': 'system',
            'content': f"""
            Jesteś asystentem, który pomaga podejmować decyzje. 
            Napisz raport dotyczący zdefiniowanego przez użytkownika problemu.
            Wykorzystaj w nim wszystkie podjęte kroki podczas podejmowania decyzji. 
            I rozwiń porady zawarte w ostatnich opcjach.
            W załączeniu masz opisany problem i kroki dojścia do ostatecznych wniosków.  
            Raport nie powinien być dłuższy niż około 2500 znaków.
            """,
        },
        {"role": "user", "content": f"""
Problem: {problem} 
Kroki: {steps}
Ostatnie opcje: {options} 
         """}
    ]
    
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )
    usage = response.usage.total_tokens
    st.session_state['total_tokens_used'] += usage
    return {"content": response}

# Funkcja do generowania drzewa decyzyjnego
def generate_decision_tree(answer):
    if answer['content'] is None:
        return {"nodes": "Błąd generowania odpowiedzi", "options": []}
    parsed_content = answer['content'].choices[0].message.parsed
    summary = parsed_content.summary
    options = [{"option": f"option {i+1}", "result": option} for i, option in enumerate(parsed_content.options)]
    return {"nodes": summary, "options": options}

with st.sidebar:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image("./pictures/logo_aidd_150.png")
    st.title("Inteligentny Asystent Decyzyjny")
    st.write("""
Aplikacja to prototyp wykorzystujący sztuczną inteligencję do generowania raportów w oparciu o dane wejściowe. 
Wyobraź sobie, że przełączymy ją na najnowszy model, a dodatkowo przeszkolony na szczegółowych danych z Twojej branży. 
Aplikacja dostosowana do Twoich procesów, specyficznych potrzeb i słownictwa, 
mogłaby znacząco usprawnić codzienne operacje, przyspieszyć analizę danych i podnieść jakość podejmowanych decyzji. 
            """)
    
    buy_me_a_coffee_button = """ <script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="jerzykozlowski" data-color="#FFDD00" data-emoji="☕" data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff"></script> """
    components.html(buy_me_a_coffee_button, height=70)

    # Footer - sidebar
    footer_style = """
        <style>
            .footer {
                bottom: 0;
                left: 0;
                right: 0;
                background-color: transparent;
                text-align: center;
                padding: 10px;
                font-size: 14px;
                border-top: 1px solid #e7e7e7;
                color: inherit;
            }
            body {
                padding-bottom: 0px;
            }
        </style>
    """
    footer_html = """
    <div class="footer">
        <p>Contact: Jerzy Kozlowski | <a href="mailto:jerzykozlowski@mailmix.pl">jerzykozlowski@mailmix.pl</a></p>
    </div>
    """
    st.markdown(footer_style, unsafe_allow_html=True)
    st.markdown(footer_html, unsafe_allow_html=True)
#
# Main
#
text_entry = st.text_area("Wprowadź opis sytuacji:", "", max_chars=250)

if 'total_tokens_used' not in st.session_state:
    st.session_state['total_tokens_used'] = 0
if "current_tree" not in st.session_state:
    st.session_state["current_tree"] = []
if "selected_option" not in st.session_state:
    st.session_state["selected_option"] = []
if "tree" not in st.session_state:
    st.session_state["tree"] = None
if "previous_steps" not in st.session_state:
    st.session_state["previous_steps"] = []
if 'selected_option_changed' not in st.session_state:
    st.session_state.selected_option_changed = False  
if "buttons_status" not in st.session_state:
    st.session_state["buttons_status"] = False

if st.button("Generuj Poradę", use_container_width=True, disabled=st.session_state["buttons_status"]):
    if text_entry.strip():
        summary = generate_next_steps(text_entry)
        tree = generate_decision_tree(summary)
        st.session_state["current_tree"].append(tree)
        st.session_state["tree"] = tree 
        # Reset selected options to ensure checkboxes are not pre-selected
        for idx in range(len(st.session_state["current_tree"])):
            st.session_state[f"selected_options_{idx}"] = []
    else:
        st.warning("Proszę wprowadzić opis sytuacji!")

for idx, node in enumerate(st.session_state["current_tree"]):
    if f"selected_options_{idx}" not in st.session_state:
        st.session_state[f"selected_options_{idx}"] = []
    st.subheader(f"Krok {idx+1}:")
    st.markdown(f"> {node['nodes']} \n * * *")
   
    # Checkbox for selecting multiple options
    updated_options = []  # Tymczasowa lista dla zaznaczonych opcji
    for idy, option in enumerate(node["options"]):
        checkbox_key = f"option_{idx}_{idy}"
        # Ensure checkboxes are not pre-selected
        checkbox_value = option["result"] in st.session_state[f"selected_options_{idx}"]
        checked = st.checkbox(option["result"], value=checkbox_value, key=checkbox_key)
        if checked:
            updated_options.append(option["result"]) 
        st.session_state[f"selected_options_{idx}"] = updated_options

    if st.button("Wybierz", key=f"select_button_{idx}", disabled=st.session_state["buttons_status"]):
        st.session_state["previous_steps"] = st.session_state["current_tree"][:idx+1]
        st.session_state["current_tree"] = st.session_state["current_tree"][:idx+1]
        st.session_state["selected_option_changed"] = True

    

# Generating next steps after selection
if st.session_state.selected_option_changed:
    all_selected_options = [
        option
        for idx in range(len(st.session_state["current_tree"]))
        for option in st.session_state[f"selected_options_{idx}"]
    ]

    if all_selected_options:
        selected_option = " ".join(all_selected_options)  # Zbiera wszystkie zaznaczone opcje
        previous_step = st.session_state["previous_steps"][-1] if st.session_state["previous_steps"] else None

        summary = generate_next_steps(selected_option, previous_step)
        new_tree = generate_decision_tree(summary)

        st.session_state["current_tree"].append(new_tree)
        st.session_state["tree"] = new_tree
        st.session_state["selected_option_changed"] = False
        st.rerun()

if st.button("Generuj Raport", use_container_width=True):      
    if st.session_state["current_tree"]:
        
        problem = st.session_state["current_tree"][0]["nodes"]
        steps = [node["nodes"] for node in st.session_state["current_tree"][1:]]
        options = [option["result"] for option in st.session_state["current_tree"][-1]["options"]]     
        report = generate_report(problem, steps, options)
        report_content = report["content"].choices[0].message.content
        st.subheader("Twój raport:")
        st.markdown(report_content)
    else:
        st.warning("Nie wygenerowano poprawnego drzewa decyzyjnego. Spróbuj jeszcze raz.")

if st.button("Resetuj Porady"):
    st.session_state["current_tree"] = []
    st.session_state["selected_option"] = []
    st.session_state["tree"] = None
    st.session_state["previous_steps"] = []
    st.session_state.selected_option_changed = False
    st.rerun()