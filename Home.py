import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from streamlit_phone_number import st_phone_number
from millify import prettify
import pandas as pd
from utils import init_connection, get_data, put_data
from datetime import datetime
import numpy as np


st.set_page_config(page_title="Kib Customers", layout="wide") 

if 'client' not in st.session_state:
    st.session_state['client'] = init_connection()
    
if 'db' not in st.session_state:
    st.session_state['db'] = st.session_state['client'].kibtoolDB

# if 'collection' not in st.session_state:
#     st.session_state['collection'] = ''

if 'dt' not in st.session_state:
    st.session_state['dt'] = datetime.now()#.isoformat()
    
# if 'data_df_cat' not in st.session_state:
#     st.session_state['collection'] = 'record_2024_Q1'
#     st.session_state["data_df_cat"] = pd.DataFrame(get_data('FarmSetup_ProductCat'))
    
def update_order_table():
    if len(st.session_state.orderTable['deleted_rows']) > 0:
        st.session_state["order_df"].drop(st.session_state.orderTable['deleted_rows'], inplace=True)
        put_data('Order', st.session_state["order_df"].to_dict("records"), 'order_log')

tab1, tab2 = st.tabs(["Order", "Log"])

with tab1:
    title,refresh = st.columns(2, vertical_alignment="bottom")
    
    title.header('Take Order')

    if refresh.button("Refresh"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

    customer_name = st.text_input('Enter the name of the customer') 

    customer_phone_number = st_phone_number("Phone", placeholder="xxxxxx ", default_country="NG")
    # st.write(customer_phone_number['number'] if customer_phone_number else '')
                
    product_dict = pd.DataFrame(get_data('FarmSetup_ProductList','record_2024_Q1')).to_dict('records')
        
    product_types= {}
    
    for d in product_dict:
        types_of_product = []
        for b in product_dict:
            if d['Product'] == b['Product']:
                types_of_product.append((b['Type'],f"{b['Weight(kg)']} kg" if not np.isnan(b['Weight(kg)']) else f"{b['Units']} units",b['Unit Price']))
        product_types[d['Product']] = types_of_product
        
    # product_types = {"**Fruits**":['Plantain', 'Breadfruit', 'Pineapple', 'Orange', 'Apple'], 
    #                  "**Animals**":['Pork', 'Chicken', 'Chicken Breat', 'Chicken Drumstick','Fish', 'Dry Fish', 'Goat', 'Sheep'],
    #                  "**Spices**":['Chilli', 'Cayenne', 'Scotch Bonnet', 'Snake Tomato'],
    #                  "**Juices**":['Palwine', 'Sugercane', 'Sugercane+Lemon+Ginger', 'Sugercane+Lime+Ginger', 'Sugercane+Lemongrass'],
    #                  "**Vegetable**":['Ewedu', 'Efo Tete', 'Efo Soko', 'Ewuro', 'Efirin', 'Igbagba'],
    #                 }

    overall_total = 0
    
    div = 3
    
    orders_picked = {}

    for ptype in product_types.items():
        with st.expander(ptype[0], expanded=False):
            rows = st.columns(div)*int(len(ptype[1])/div) if not len(ptype[1])%div else st.columns(div)*(int(len(ptype[1])/div)+1)

            for col, product in zip(rows,ptype[1]):
                tile = col.container(height=370)
                prod, units, pick = tile.columns([0.4,0.35,0.25], vertical_alignment="center")
                prod.text(product[0])
                units.text(f'{product[1]} left')
                picked = pick.checkbox('select', key='sel '+product[0])
                
                tile.page_link("https://streamlit.io/gallery", label=f"{product[0]}", icon=":material/add_circle:", help=f'Get more information on our {product[0]}')
                
                # tile.selectbox("Category", ('small', 'medium', 'big'), key='cat '+product, disabled=not picked)
                unit_p = tile.number_input("Unit Price", value=product[2], key='unit '+product[0], disabled=not picked) # unit price per kg
                quantity = tile.number_input(f"Quantity({product[1].split(' ')[1]})", key='quant '+product[0], disabled=not picked) # the max_value depends on the total number of the item or kg available 
                total = tile.number_input("Total Price", value=unit_p*quantity, key='tp '+product[0], disabled=not picked) # a computation of quantity and unit price
                overall_total += total if picked else 0.0 
                
                if picked:
                    orders_picked.update({product[0]:[unit_p, quantity, total]})
                elif not picked:
                    orders_picked.pop(product[0], [])

    st.number_input("Overall Total", value=overall_total)
    
    f'The overall cost of your order is: N{prettify(overall_total)}'
    
    paymode = st.selectbox("Payment mode", ('POS', 'Transfer', 'Cash', 'PayMeLater'), key='paymode')
    
    with st.popover('Order Summary', disabled=True if not orders_picked else False):
        df = pd.DataFrame(orders_picked, index=['Unit Price(N)',f'Qunatity(units/kg)','Total(N)'])
        st.dataframe(df)
        
    _,refresh = st.columns(2)
        
    # send order to db after payment
    if refresh.button('Conclude Order', disabled=True if not orders_picked else False): 
        for k,v in orders_picked.items(): 
            v.append(paymode)
            v.append(customer_name)
            v.append(customer_phone_number['number'] if customer_phone_number else '')
            v.append(datetime.now())
            orders_picked[k] = v
            
        # records = [(k, v) for k, v in orders_picked.items()]
        
        
        df = pd.DataFrame(orders_picked)
        df = df.transpose()
        df = df.reset_index(names='Product')
        df = df.rename(columns={0:'Unit Price',1:'Qunatity',2:'Total',3:'Payment Method',
                                4:'Customer Name',5:'Customer Number', 6:'Date'})
        
        df_from_db = pd.DataFrame(get_data('Order','order_log'))
                        
        new_df = df if df_from_db.empty else pd.concat([df_from_db, df], ignore_index=True)
            
        put_data('Order', new_df.to_dict("records"), 'order_log')
        
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
        
            
        # st.write(df)
        
with tab2:
    with st.status("", expanded=True) as status:
        if st.button("Save", key="order_but"):
            status.update(label="uploading data...", state="running")
            put_data('Order', st.session_state["order_df"].to_dict("records"), 'order_log')
            status.update(label="upload complete!", state="complete")
                    
        st.session_state["order_df"] = st.data_editor(pd.DataFrame(get_data('Order','order_log')), num_rows="dynamic", key="orderTable", on_change=update_order_table)
        
        
