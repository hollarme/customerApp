import streamlit as st

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# (kibtool) imachine@imachine:~$ mongosh "mongodb+srv://cluster0.lhxokzx.mongodb.net/" --apiVersion 1 --username bovenssolutions
# st.write(st.secrets["mongo"]["uri"])

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    # Create a new client and connect to the server
    return MongoClient(str(st.secrets["mongo"]["uri"]), server_api=ServerApi('1'))
    # return pymongo.MongoClient(**st.secrets["mongo"], authSource="admin")


# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
# @st.cache_data(ttl=600)
def get_data(name, collection):
    db = st.session_state['db']
    # collection = st.session_state['collection']
    item = db[collection].find_one({'name':name})
    # items = list(items)  # make hashable for st.cache_data
    return item['data'] if item else None


# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
# @st.cache_data(ttl=600)
def put_data(name, data, collection):
    db = st.session_state['db']
    # collection = st.session_state['collection']
    db[collection].replace_one({'name':name},{'name':name, 'data':data},True)
    
