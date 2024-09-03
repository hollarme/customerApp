import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from streamlit_phone_number import st_phone_number
from millify import prettify
import pandas as pd
from utils import init_connection, get_data, put_data
from datetime import datetime
import numpy as np
# from mitosheet.streamlit.v1 import spreadsheet
import random


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
        
def update_product_table():
        if len(st.session_state.prolistTable['deleted_rows']) > 0:
            st.session_state["data_df"].drop(st.session_state.prolistTable['deleted_rows'], inplace=True)
            put_data('Order', st.session_state["data_df"].to_dict("records"), 'order_log')

@st.dialog("Price Change")
def rebate(key, price):
    st.write(f'The new value is:{st.session_state[key]}')
    # update rebate check box
    ksplit = key.split(' ')
    a = ksplit[0]
    b = ' '.join(ksplit[1:])
    st.warning(f'Are you giving a rebate on the {a} price for {b}? If so check the rebate box for {b}', icon="⚠️")

tab1, tab2, tab3 = st.tabs(["Order", "Log", "Product"])

with tab1:
    
    title,refresh = st.columns(2, vertical_alignment="bottom")
    
    title.header('Take Order')

    if refresh.button("Refresh"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

    customer_name = st.text_input('Enter the name of the customer') 

    customer_phone_number = st_phone_number("Phone", placeholder="xxxxxx ", default_country="NG")
    # st.write(customer_phone_number['number'] if customer_phone_number else '')
                
    # product_dict = pd.DataFrame(get_data('FarmSetup_ProductList','record_2024_Q1')).to_dict('records')
    product_dict = pd.DataFrame(get_data('Order_ProductList','order_log')).to_dict('records')

        
    product_types= {}
    
    for d in product_dict:
        types_of_product = []
        for b in product_dict:
            if d['Product'] == b['Product']:
                types_of_product.append((b['Type'], b['Tag'], f"{b['Weight(kg)']} kg" if not np.isnan(b['Weight(kg)']) else f"{int(b['Units'])} units",b['Unit Price']))
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
                # st.write(product[1]==None)
                tile = col.container(height=400)
                prod, units, pick = tile.columns([0.5,0.3,0.2], vertical_alignment="center")
                prod.page_link("https://streamlit.io/gallery", label="{} ({})".format('\n\n'.join(product[0].split('+')), product[1]), icon=":material/forward:", help=f'Get more information on our {product[0]}')
                units.text(f'{product[2]} left')
                picked = pick.checkbox('select', key='sel '+product[0] if product[1]==None else 'sel '+product[0]+product[1])
                
                # tile.page_link("https://streamlit.io/gallery", label=f"{product[0]}", icon=":material/Foward:", help=f'Get more information on our {product[0]}')
                
                # tile.selectbox("Category", ('small', 'medium', 'big'), key='cat '+product, disabled=not picked)
                unit_p = tile.number_input("Unit Price", value=product[3], key='unit '+product[0] if product[1]==None else 'unit '+product[0]+product[1], disabled=not picked, on_change=rebate, max_value=product[3], args=['unit '+product[0] if product[1]==None else 'unit '+product[0]+product[1], product[3]]) # unit price per kg
                
                quantity = tile.number_input(f"Quantity({product[2].split(' ')[1]})", value=0.0 if product[2].split(' ')[1]=='kg' else 0 ,key='quant '+product[0] if product[1]==None else 'quant '+product[0]+product[1], disabled=not picked, max_value=eval(product[2].split(' ')[0])) # the max_value depends on the total number of the item or kg available 
                
                total = tile.number_input("Total Price", value=unit_p*quantity, key='total '+product[0] if product[1]==None else 'total '+product[0]+product[1], disabled=not picked, on_change=rebate, args=['total '+product[0] if product[1]==None else 'total '+product[0]+product[1], unit_p*quantity]) # a computation of quantity and unit price
                
                reb = tile.checkbox('rebate', key='reb '+product[0] if product[1]==None else 'reb '+product[0]+product[1], value=False, disabled=not picked)
                
                overall_total += total if picked else 0.0 
                
                if picked:
                    orders_picked.update({f"{product[0]}({product[1]})":[unit_p, quantity, total, reb]})
                elif not picked:
                    orders_picked.pop(f"{product[0]}({product[1]})", [])

    st.number_input("Overall Total", value=overall_total, key='ovt', on_change=rebate, args=['ovt', st])
    st.checkbox('rebate', key='reb ovt', value=False, disabled=False)
    
    f'The overall cost of your order is: N{prettify(overall_total)}'
    
    paymode = st.selectbox("Payment mode", ('POS', 'Transfer', 'Cash', 'PayMeLater'), key='paymode')
    
    with st.popover('Order Summary', disabled=True if not orders_picked else False):
        df = pd.DataFrame(orders_picked, index=['Unit Price(N)',f'Qunatity(units/kg)','Total(N)', 'Rebate'])
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
        df = df.rename(columns={0:'Unit Price',1:'Qunatity',2:'Total',3:'Rebate',4:'Payment Method',
                                5:'Customer Name', 6:'Customer Number', 7:'Date'})
        
        df_from_db = pd.DataFrame(get_data('Order','order_log'))
                        
        new_df = df if df_from_db.empty else pd.concat([df_from_db, df], ignore_index=True)
            
        put_data('Order', new_df.to_dict("records"), 'order_log')
        
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
        
            
        # st.write(df)
        
with tab2:
    with st.status("", expanded=True) as status:
        
        st.title("Order Log")
        
        if st.button("Save", key="order_but"):
            status.update(label="uploading data...", state="running")
            put_data('Order', st.session_state["order_df"].to_dict("records"), 'order_log')
            status.update(label="upload complete!", state="complete")
            
        interface = st.radio("",['Table Interface', 'MitoSheet Interface'],horizontal=True, key="inc_radio")
        
        if interface == "Table Interface":           
            st.session_state["order_df"] = st.data_editor(pd.DataFrame(get_data('Order','order_log')), num_rows="dynamic", key="orderTable", on_change=update_order_table)
            
        elif interface == "MitoSheet Interface":
            pass
            # dataframe, code = spreadsheet(st.session_state["order_df"])
            # st.code(code)
        
        
with tab3:
    
    with st.status("", expanded=True) as status:

        st.title("Product List")
        
        if st.button("Save", key="plist_but"):
            status.update(label="uploading data...", state="running")
            put_data('Order_ProductList', st.session_state["data_df"].to_dict("records"), 'order_log')
            status.update(label="upload complete!", state="complete")

        st.session_state["data_df"] = pd.DataFrame(get_data('Order_ProductList', 'order_log'))

        if st.session_state["data_df"].empty:

            st.session_state["data_df"] = pd.DataFrame(
                {
                    "Product": [""],
                    "Type": [""],
                    "Tag": [""],
                    "Weight(kg)": [None],
                    "Units":[None],
                    "Unit Price":[0.0],
                    'Date':[st.session_state['dt']],
                    'Note':[""]
                    # "Unit Price (N)": [""]
                }
            )

        st.session_state["data_df"] = st.data_editor(
            st.session_state["data_df"],
            column_config={
                "Product":  st.column_config.TextColumn(required=True),
                "Type":  st.column_config.TextColumn(required=True),
                "Tag":  st.column_config.TextColumn(required=False), 
                "Weight(kg)": st.column_config.NumberColumn(default=None),
                "Units": st.column_config.NumberColumn(default=None),
                "Unit Price":st.column_config.NumberColumn(default=0.0),
                "Date": st.column_config.DateColumn(required=True, default=datetime.date(datetime.now())),
                # "Note": st.column_config.TextColumn()
            },

            num_rows="dynamic",
            key="prolistTable",
            on_change=update_product_table
        )

# #                         st.subheader("Product List After Transactions")

# #                         or_df = st.session_state["data_df"][pd.to_datetime(st.session_state["data_df"]['Date']).dt.date == datetime.date(datetime.now())]
# #                         co_df = st.session_state["tran_data_df"][pd.to_datetime(st.session_state["tran_data_df"]['Date']).dt.date == datetime.date(datetime.now())]
# #                         co_df['Units'] *= -1
# #                         co_df['Weight(kg)'] *= -1
# #                         pp_df = pd.concat([or_df.loc[:,('Category', 'Product', 'Type', 'Weight(kg)','Units')], co_df.loc[:,('Category', 'Product', 'Type', 'Weight(kg)','Units')]])
# #                         st.dataframe(pp_df.groupby(['Category', 'Product', 'Type']).sum())

#     else:
#         b_df = st.session_state["data_df_cat"]
#         category = st.selectbox("select the product category", set(b_df['Category'].tolist()))
#         product = st.selectbox("select the product", set(b_df.loc[b_df['Category']==category]['Product'].tolist()))
#         type = st.selectbox("select the product type if available", set(b_df.loc[(b_df['Category']==category)&(b_df['Product']==product)]['Type'].tolist()))
#         weight = st.number_input("Enter the products weight in kg")
#         unit = st.number_input("Number of units available")
#         unit_price = st.number_input("Enter the price for a single unit")
#         date = st.date_input(label="Enter start date") 
#         time = datetime.time(datetime.now())#st.time_input('', value="now", disabled=True)
#         dt = datetime.combine(date, time)#.isoformat()
#         note = st.text_area("Enter extra information")

#         st.session_state['pro_list_table'] = {'Category': category, 'Product': product, 'Type': type, 'Weight(kg)': weight,'Units': unit, "Unit Price":unit_price,'Date':st.session_state['dt'], 'Note': note, "Date":dt}
