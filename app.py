import streamlit as st
import pyrebase
from stmol import showmol
import py3Dmol
import biotite.structure.io as bsio
import requests
from firebase_config import config

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()


header_section = st.container()
main_section = st.container()
auth_section = st.container()
logout_section = st.container()


def auth_sidebar():
    main_section.empty()
    menu = ['Login', 'Sing Up', 'Forgot password']
    choice = st.sidebar.selectbox('Login/Sing Up', menu)
    if choice == 'Login':
        show_login()
    elif choice == 'Sing Up':
        show_sign_up()
    elif choice == 'Forgot password':
        show_forgot_password()


def login(email, pwd):
    try:
        auth.sign_in_with_email_and_password(email, pwd)
        st.success(':white_check_mark: Successfully logged in!')
        st.session_state.logged_in = True
    except:
        st.session_state.logged_in = False
        st.warning(":bulb: Invalid email or password")


def show_login():
    with auth_section:
        st.title('Login')

        # form = st.form(key='login_form')
        email = st.text_input('Email Address')
        pwd = st.text_input('Password', type='password')
        st.button('Login', type='secondary', on_click=login, args=(email, pwd))


def sign_up(email, pwd):
    try:
        user = auth.create_user_with_email_and_password(email, pwd)
        st.success(':white_check_mark: Successfully created account! Try login')
    except Exception as e:
        err = str(e.args[1])
        if err.__contains__("Password should be"):
            st.warning(':bulb: Password should be at least 6 characters. Try again!')
        elif err.__contains__("EMAIL_EXISTS"):
            st.warning(':bulb: Email already exist!')
        elif err.__contains__("INVALID_EMAIL"):
            st.warning(':bulb: Invalid email. Try again!')
        elif err.__contains__("MISSING_PASSWORD"):
            st.warning(':bulb: Missing password!')
        elif err.__contains__("MISSING_EMAIL"):
            st.warning(':bulb: Missing email!')
        else:
            st.error(':bulb: Unexpected error. Try later.')


def show_sign_up():
    with auth_section:
        st.title('Sing Up')

        # form = st.form(key='signup_form')
        email = st.text_input('Email Address')
        pwd = st.text_input('Password', type='password', placeholder='At least 6 characters')
        st.button('Sing up', type='secondary', on_click=sign_up, args=(email, pwd))


def show_forgot_password():
    st.title('Forgot Password')

    email = st.text_input('Email Address')
    submit = st.button('Send email', type='secondary')
    if submit:
        try:
            auth.send_password_reset_email(email)
            st.success(':white_check_mark: Email sent!')
        except Exception as e:
            err = str(e.args[1])
            st.write(err)
            if err.__contains__("EMAIL_NOT_FOUND"):
                st.warning(':bulb: Unregistered email. Try again!')
            elif err.__contains__("INVALID_EMAIL"):
                st.warning(':bulb: Invalid email. Try again!')
            elif err.__contains__("MISSING_EMAIL"):
                st.warning(':bulb: Missing email!')
            else:
                st.error(':exclamation: Unexpected error. Try later.')


def logout():
    st.session_state.logged_in = False


def show_logout():
    auth_section.empty()
    with logout_section:
        st.sidebar.button('Logout', on_click=logout)


def render_mol(pdb):
    pdbview = py3Dmol.view()
    pdbview.addModel(pdb, 'pdb')
    pdbview.setStyle({'cartoon': {'color': 'spectrum'}})
    pdbview.setBackgroundColor('white')  # ('0xeeeeee')
    pdbview.zoomTo()
    pdbview.zoom(2, 800)
    pdbview.spin(True)
    showmol(pdbview, height=500, width=800)


def update(sequence):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = requests.post('https://api.esmatlas.com/foldSequence/v1/pdb/', headers=headers, data=sequence)
    # name = sequence[:3] + sequence[-3:]
    pdb_string = response.content.decode('utf-8')

    with open('data/predicted.pdb', 'w') as f:
        f.write(pdb_string)

    try:
        struct = bsio.load_structure('data/predicted.pdb', extra_fields=["b_factor"])
        b_value = round(struct.b_factor.mean(), 4)
    except:
        st.error('The file has 0 models, the given model 1 does not exist.')
        st.sidebar.warning(':point_up: Try another sequence!')
        st.stop()

    # Display protein structure
    st.subheader('Visualization of predicted protein structure')
    render_mol(pdb_string)

    # plDDT value is stored in the B-factor field
    st.subheader('plDDT')
    st.write('plDDT is a per-residue estimate of the confidence in prediction on a scale from 0-100.')
    st.info(f'plDDT: {b_value}')

    st.download_button(
        label="Download PDB",
        data=pdb_string,
        file_name='data/predicted.pdb',
        mime='text/plain',
    )


def show_main():
    with main_section:
        st.sidebar.title("ESMFold")
        st.sidebar.markdown(
            '''
                [*ESMFold*](https://esmatlas.com/about) is an end-to-end single sequence protein structure predictor based on the 
                ESM-2 language model. For more information, read the [research article](https://www.biorxiv.org/content/10.1101/2022.07.20.500902v2) 
                and the [news article](https://www.nature.com/articles/d41586-022-03539-1) published in *Nature*.
            ''')
        # Protein sequence input
        DEFAULT_SEQUENCE = "MGSSHHHHHHSSGLVPRGSHMRGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPRLASHGFVVITIDTNSTLDQPSSRSSQQMAALRQVASLNGTSSSPIYGKVDTARMGVMGWSMGGGGSLISAANNPSLKAAAPQAPWDSSTNFSSVTVPTLIFACENDSIAPVNSSALPIYDSMSRNAKQFLEINGGSHSCANSGNSNQALIGKKGVAWMKRFMDNDTRYSTFACENPNSTRVSDFRTANCSLEDPAANKARKEAELAAATAEQ"
        txt = st.sidebar.text_area('**Input sequence:**', DEFAULT_SEQUENCE, height=275)
        # predict function button
        predict = st.sidebar.button('Predict')
        if predict:
            update(txt)
        else:
            st.warning('👈 Enter protein sequence data!')


with header_section:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        auth_sidebar()
    else:
        if st.session_state.logged_in:
            show_logout()
            show_main()
        else:
            auth_sidebar()

