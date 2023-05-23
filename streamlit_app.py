###
###    Description: 
###    Streamlit app to search a user query in Found reports 
###    using Vector Similarity Search (VSS) with Azure OpenAI Embeddings
###    in a Redis database documents.
###
###    ** Make sure to connect to the Redis server  before running the app.
###    ** Last update 05/22/23

import os
import openai
import numpy as np
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

from openai.embeddings_utils import get_embeddings
from redis import Redis
from redis.commands.search.field import TagField, VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

#Define the Redisearch index name & Redis server connection
INDEX_NAME  = os.getenv("INDEX_NAME") 
HOST        = os.getenv("REDIS_HOST") 
PORT        = os.getenv("REDIS_PORT")

# Define Azure openai parameters
EMBEDDING_MODEL     = os.getenv("EMBEDDING_MODEL")
openai.api_type     = os.getenv("API_TYPE") 
openai.api_version  = os.getenv("API_VERSION")
openai.api_key      = os.getenv("API_KEY")
openai.api_base     = os.getenv("API_BASE")


# Connect to Redis
r = Redis(host=HOST, port=PORT)
if r.ping():
    print("Redis connection successful")

@st.cache_data


#Function to get embeddings from query text with Azure OpenAI
def get_embedding(text, engine=EMBEDDING_MODEL):
    """
    Get the embeddings for a given text using the OpenAI API
    Arguments:
        text: a string, the text to embed
        engine: Embedding model to use
    Returns:
        embeddings: a list of floats, the embeddings for the text
    """
    response = openai.Embedding.create(
                input=text,
                engine=EMBEDDING_MODEL
               )
    embeddings = response['data'][0]['embedding']

    return embeddings

# Streamlit app main function
def main():
    """
    This app main function
    Arguments:
        None
    Returns:
        Builds the UI with streamlit
    """

    #st.image(os.path.join('images','LOGO-Chargerback-LNFS-72.png'))
    st.image('architecture.png')

    st.title("Vector Similarity Search")
    body="""
    ## Vector Similatity Search with Azure OpenAI Embeddings

    This demo allows us to search a Redis database of approx. 100,000 Found reports 
    using Vector Similarity Search via vector embedings.

    Here we are using `Azure OpenAI Embeddings` vector transformer 
    with COSINE similarity saved on a Redis database. Unlike full text search - vector embedding is capable of matching texts that 
    has similar meaning or theme, but not nessesarily using the same words.

    To see the search results, try different combination of the search terms and Partner IDs. For instance:

    - I lost my iPhone 14 **AND** Partner ID 6392
    - I lost my Disney hat **AND** Partner ID 16130
    - My name is JD Lippard and my wallet is missing **AND**  Partner ID 6392
    

    """

    with st.expander('About this demo:', expanded=False):
        st.markdown(body)
    
    user_query = st.text_input("Query:", 'I lost a Blue Samsung Galaxy, screen sever with agriculture field and blue sky.')
    
    
    #partner_id = st.selectbox('Select Partner ID:',('6392', '16130'))
    partner_id = st.radio('Select Partner ID:',('00000','6392', '16130'))

    #For demo purposes only, we are using a fixed Partner ID
    if partner_id=='6392' or partner_id=='16130':
        embedding = get_embedding(user_query)
        query_embedding = np.array(embedding).astype(np.float32)

        query = (
            #Query(f"(@tag:{{ Found }}) {search_query}=>[KNN 2 @vector $vec as score]")
            Query(f"(@PartnerID:{{{partner_id}}} @tag:{{Found}})=>[KNN 5 @vector $vec as score]")
             .sort_by("score")
             .return_fields("Description", "Item", "PartnerID", "score")
             .paging(0, 5)
             .dialect(2)
        )

        # Define the query parameters
        query_params = {"vec": query_embedding.tobytes()}

        # Execute the Redisearch query
        result = r.ft(INDEX_NAME).search(query, query_params).docs
    

        # Display the search results
        st.subheader(f"Query: {user_query}")
        for doc in result:
            st.write(f"Item: {doc.Item}")
            st.write(f"Description: {doc.Description}")
            st.write(f"Partner ID: {doc.PartnerID}")
            st.write(f"Score: {doc.score}")
            st.write("")
            st.write("- - - - - - - - - - -  - - - - ")
            st.write("")

#Call the main function
if __name__ == '__main__':
    main()