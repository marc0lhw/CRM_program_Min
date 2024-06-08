import streamlit as st
import sqlite3
import pandas as pd
import re
import datetime
from pytz import timezone
from streamlit_option_menu import option_menu
import streamlit.components.v1 as html
from  PIL import Image
import numpy as np
import plotly.express as px
import io

def create_connection():
    conn = sqlite3.connect('customer_management.db')
    return conn

# 고객 추가 함수
def add_customer(name, phone):
    conn = create_connection()
    c = conn.cursor()
    c.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()
    conn.close()

# 고객 조회 함수
def get_customer_by_name_or_phone(name=None, phone=None):
    conn = create_connection()
    c = conn.cursor()
    if name:
        c.execute("SELECT * FROM customers WHERE name LIKE ? and deleted_status != '삭제'", ('%' + name + '%',))
        customers = c.fetchall()
    elif phone:
        c.execute("SELECT * FROM customers WHERE phone = ? and deleted_status != '삭제'", (phone,))
        customers = c.fetchone()
    conn.close()
    return customers

# 고객 수신거부 함수
def refusal_customer(customer_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET refusal_status = '거부됨' WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

# 고객 삭제 함수
def delete_customer(customer_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET deleted_status = '삭제' WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

# 고객 명단 조회 함수
def get_all_customers():
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        WITH agg as
        (
            SELECT customer_id, sum(amount) as total_amount
            FROM purchases
            WHERE payment_method != '마일리지'
            GROUP BY customer_id
        )
        SELECT customers.name, customers.phone, customers.mileage,
               case
                when(agg.total_amount is null) then 0
                else agg.total_amount
               end as total_amount
        FROM customers
        LEFT JOIN agg
            ON customers.id = agg.customer_id
        WHERE deleted_status != '삭제'
    """)
    customers = c.fetchall()
    conn.close()
    return customers

# 고객 명단 조회 함수
def get_all_customers_for_csv():
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT phone, name, group_type, refusal_status FROM customers WHERE deleted_status != '삭제'")
    customers = c.fetchall()
    conn.close()
    return customers

# 고객 명단 내보내기 함수
def export_customers_to_csv():
    customers = get_all_customers_for_csv()
    df = pd.DataFrame(customers, columns=['전화번호', '이름', '그룹', '거부유무'])
    filename = f"customer_list_{datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    return filename

#매출 조회 함수
def get_sales_data(view_option):
    conn = create_connection()
    c = conn.cursor()

    if view_option == "일별":
        start_date = datetime.datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%d")
        end_date = (datetime.datetime.now(timezone('Asia/Seoul')) + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif view_option == "월별":
        start_date = datetime.datetime.now(timezone('Asia/Seoul')).replace(day=1).strftime("%Y-%m-%d")
        end_date = (datetime.datetime.now(timezone('Asia/Seoul')) + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        start_date = datetime.datetime.now(timezone('Asia/Seoul')).replace(month=1, day=1).strftime("%Y-%m-%d")
        end_date = (datetime.datetime.now(timezone('Asia/Seoul')) + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    
    # 조회 기간에 따라 데이터베이스에서 데이터를 가져옴
    c.execute("SELECT purchases.id, purchases.customer_id, customers.name, purchases.amount, purchases.payment_method, purchases.date FROM purchases JOIN customers ON purchases.customer_id = customers.id AND purchases.payment_method != '마일리지' AND purchases.date BETWEEN '%s' AND '%s'" % (start_date, end_date))
    
    purchases = c.fetchall()

    c.execute("SELECT refunds.id, refunds.customer_id, customers.name, refunds.amount, refunds.date FROM refunds JOIN customers ON refunds.customer_id = customers.id AND refunds.date BETWEEN '%s' AND '%s'" % (start_date, end_date))
    refunds = c.fetchall()
    
    conn.close()
    
    return purchases, refunds

def get_customer_purchases(customer_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT amount, payment_method, date FROM purchases WHERE customer_id = ?", (customer_id,))
    purchases = c.fetchall()
    conn.close()
    return purchases

def get_customer_refunds(customer_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT amount, date FROM refunds WHERE customer_id = ?", (customer_id,))
    refunds = c.fetchall()
    conn.close()
    return refunds


# Streamlit UI 설정
#st.sidebar.title("고객 관리 프로그램")

#menu = ["고객 조회", "고객 추가", "고객 명단 조회", "고객 명단 내보내기", "매출 조회"]
#choice = st.sidebar.radio("메뉴 선택", menu)

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 220px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    choice = option_menu("Min 고객관리", ["고객 조회", "고객 추가", "고객 명단 조회", "고객 명단 내보내기", "매출 조회"],
                         menu_icon="house", default_index=0,
                         styles={
        "container": {"padding": "0!important", "background-color": "#fafafa", "width":"190px"},
        "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#02ab21"},
        "menu-title": {  # Add this style block for the menu title
            "font-size": "22px",  # Adjust the font size
            "font-weight": "bold",  # Adjust the font weight
            "margin": "0px"  # Adjust the margin
        }
    }
    )


if choice == "고객 조회":
    st.title("고객 조회")
        
    # 화면 분할
    col1, empty_col, col2, empty_col2 = st.columns([1, 0.1, 1, 0.1])
    empty_col.empty()
    empty_col2.empty()
    
    search_option = col1.radio("<검색 옵션>", ("이름", "핸드폰 번호"))
    search_value = col1.text_input(f"{search_option} 입력").strip()

    if col1.button("조회"):
        if search_option == "이름":
            customer = get_customer_by_name_or_phone(name=search_value)
            
            if len(customer)>1:
                col1.warning("이름이 겹치는 고객이 존재합니다. 핸드폰 번호로 검색해주세요.")
                customer = False
            elif customer == []:
                customer = None
            else:
                customer=customer[0] 
                
        else:
            if not re.match(r"^010-\d{4}-\d{4}$", search_value):
                col1.error("올바른 핸드폰 번호 형식이 아닙니다. (예: 010-1234-5678)")
                customer = False
            else:
                customer = get_customer_by_name_or_phone(phone=search_value)
 
        st.session_state['selected_customer'] = customer
    
    if 'selected_customer' in st.session_state:
        customer = st.session_state['selected_customer']
        
        if customer:
            col1.success("고객 정보를 불러왔습니다. 하단의 버튼들 중 하나를 선택하세요.")
            col2.subheader("고객정보")
            col2.write(f"이름: {customer[1]}")
            col2.write(f"전화번호: {customer[2]}")
            col2.write(f"마일리지: {customer[3]}")
            col2.write("---")

            col1.write("---")

            sub_col1, sub_col2, sub_col3= col1.columns([0.8, 1, 1])
            
            if sub_col1.button('제품 구매'):
                st.session_state['purchase_mode'] = True
                st.session_state['refund_mode'] = False
                st.session_state['use_mileage_mode'] = False
                st.session_state['del_customer_mode'] = False
                st.session_state['refusal_setting_mode'] = False

            if sub_col2.button('제품 환불'):
                st.session_state['purchase_mode'] = False
                st.session_state['refund_mode'] = True
                st.session_state['use_mileage_mode'] = False
                st.session_state['del_customer_mode'] = False
                st.session_state['refusal_setting_mode'] = False

            if sub_col3.button('마일리지 사용'):
                st.session_state['purchase_mode'] = False
                st.session_state['refund_mode'] = False
                st.session_state['use_mileage_mode'] = True
                st.session_state['del_customer_mode'] = False
                st.session_state['refusal_setting_mode'] = False

            if sub_col1.button('고객 삭제'):
                st.session_state['purchase_mode'] = False
                st.session_state['refund_mode'] = False
                st.session_state['use_mileage_mode'] = False
                st.session_state['del_customer_mode'] = True
                st.session_state['refusal_setting_mode'] = False
                
            if sub_col2.button('문자 수신거부'):
                st.session_state['purchase_mode'] = False
                st.session_state['refund_mode'] = False
                st.session_state['use_mileage_mode'] = False
                st.session_state['del_customer_mode'] = False
                st.session_state['refusal_setting_mode'] = True
                
            col2.subheader("구매 내역")
            purchases = get_customer_purchases(customer[0])
            df_purchases = pd.DataFrame(purchases, columns=['Amount', 'Payment Method', 'Date                                        '])
            col2.dataframe(df_purchases, height=300)

            col2.subheader("환불 내역")
            refunds = get_customer_refunds(customer[0])
            df_refunds = pd.DataFrame(refunds, columns=['Amount', 'Date                                        '])
            col2.dataframe(df_refunds, height=300   )
            
        elif customer==False:
            col1.write("---")
            
        else:
            col1.error("사용자가 존재하지 않습니다.")
            st.session_state['purchase_mode'] = False
            st.session_state['refund_mode'] = False
            st.session_state['use_mileage_mode'] = False
            st.session_state['del_customer_mode'] = False
            st.session_state['refusal_setting_mode'] = False
        
        if st.session_state.get('purchase_mode', False):
            col1.write("---")
            purchase_amount = col1.number_input("구매 금액 입력", min_value=0, format="%d")
            payment_method = col1.radio("결제 방식 선택", ("현금", "카드"))
            mileage_method = col1.radio("마일리지 적립 여부 선택", ("적립", "미적립"))
            if col1.button("구매 확정"):
                conn = create_connection()
                c = conn.cursor()
                c.execute("INSERT INTO purchases (customer_id, amount, payment_method) VALUES (?, ?, ?)", (customer[0], purchase_amount, payment_method))
                if(mileage_method == "적립"):
                    c.execute("UPDATE customers SET mileage = mileage + ? WHERE id = ?", (purchase_amount * 0.01, customer[0]))
                conn.commit()
                conn.close()
                if(mileage_method == "적립"):
                    col1.success("구매 완료 및 마일리지 적립 완료")
                else:
                    col1.success("구매 완료 및 마일리지 미적립 완료")
                st.session_state['purchase_mode'] = False

        if st.session_state.get('refund_mode', False):
            col1.write("---")
            refund_amount = col1.number_input("환불 금액 입력", min_value=0, format="%d")
            mileage_method = col1.radio("마일리지 차감 여부 선택", ("차감", "미차감"))
            if col1.button("환불 확정"):
                conn = create_connection()
                c = conn.cursor()
                c.execute("INSERT INTO refunds (customer_id, amount) VALUES (?, ?)", (customer[0], refund_amount))
                if(mileage_method == "차감"):
                    c.execute("UPDATE customers SET mileage = mileage - ? WHERE id = ?", (refund_amount * 0.01, customer[0]))
                conn.commit()
                conn.close()
                if(mileage_method == "차감"):
                    col1.success("환불 완료 및 마일리지 차감 완료")
                else:
                    col1.success("환불 완료 및 마일리지 미차감 완료")
                st.session_state['refund_mode'] = False

        if st.session_state.get('use_mileage_mode', False):
            col1.write("---")
            mileage_use_amount = col1.number_input("사용할 마일리지 금액 입력", min_value=0, format="%d")
            if col1.button("사용 확정"):
                conn = create_connection()
                c = conn.cursor()
                c.execute("INSERT INTO purchases (customer_id, amount, payment_method) VALUES (?, ?, ?)", (customer[0], mileage_use_amount, '마일리지'))
                c.execute("UPDATE customers SET mileage = mileage - ? WHERE id = ?", (mileage_use_amount, customer[0]))
                conn.commit()
                conn.close()
                col1.success("마일리지 사용 완료")
                st.session_state['use_mileage_mode'] = False
    
        if st.session_state.get('del_customer_mode', False):
            col1.write("---")
            col1.warning("정말 고객을 삭제하시겠습니까?")
            
            if col1.button("확인"):
                delete_customer(customer[0])
                col1.success("고객이 삭제되었습니다.")
                st.session_state['confirm_delete'] = False
            if col1.button("취소"):
                col1.success("삭제가 취소되었습니다.")
                st.session_state['confirm_delete'] = False
                
        if st.session_state.get('refusal_setting_mode', False):
            col1.write("---")
            col1.warning("정말 문자 수신을 거부 하시겠습니까?")
            
            if col1.button("확인"):
                refusal_customer(customer[0])
                st.session_state['refusal_setting_mode'] = False
                col1.success("문자 수신 거부 완료")
            if col1.button("취소"):
                col1.success("문자 수신 거부 시도가 취소되었습니다.")
                st.session_state['refusal_setting_mode'] = False


elif choice == "고객 추가":
    st.title("고객 추가")
    # 화면 분할
    col1, empty_col, col2 = st.columns([1, 0.1, 1])
    empty_col.empty()
    
    name = col1.text_input("이름").strip()
    phone = col1.text_input("핸드폰 번호").strip()
    if col1.button("추가"):
        if not re.match(r"^010-\d{4}-\d{4}$", phone):
            col1.error("올바른 핸드폰 번호 형식이 아닙니다. (예: 010-1234-5678)")
        else:
            if get_customer_by_name_or_phone(name=name) != None:
                col1.error("이름이 중복되는 고객입니다.")
            elif get_customer_by_name_or_phone(phone=phone) != None:
                col1.error("전화번호가 중복되는 고객입니다.")
            else:
                add_customer(name, phone)
                customer = get_customer_by_name_or_phone(name=name)
                col2.subheader("고객정보")
                col2.write(f"이름: {customer[1]}")
                col2.write(f"전화번호: {customer[2]}")
                col2.write(f"마일리지: {customer[3]}")
                col2.write("---")
                col1.success("고객 추가 완료")

elif choice == "고객 명단 조회":
    st.title("고객 명단 조회")
    customers = get_all_customers()
    df_customers = pd.DataFrame(customers, columns=['이름', '전화번호', '마일리지', '누적 구매금액'])
    st.dataframe(df_customers, height=700, width=800)

elif choice == "고객 명단 내보내기":
    st.title("고객 명단 내보내기")
    if st.button("CSV 내보내기"):
        filename = export_customers_to_csv()
        st.success(f"{filename} 파일이 성공적으로 저장되었습니다.")

elif choice == "매출 조회":
    st.title("매출 조회")
    # 화면 분할 
    col1, empty_col, col2 = st.columns([1, 0.1, 1])
    empty_col.empty()
    
    view_option = col1.radio("<조회 옵션>", ("일별", "월별", "년별"))
    if view_option == "일별":
        date_format = "%Y-%m-%d"
        now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
    elif view_option == "월별":
        date_format = "%Y-%m-%d"
        now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y년 %m월')
    else:
        date_format = "%Y-%m"
        now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y년')

    purchases, refunds = get_sales_data(view_option)
   
    col1.write("---")
    # 구매 내역 총합
    total_purchase = int(sum([purchase[3] for purchase in purchases]))

    # 환불 내역 총합
    total_refund = int(sum([refund[3] for refund in refunds]))

    # 총합 출력
    total_sales = total_purchase - total_refund
    
    # 손님 수
    names = list(set([purchase[1] for purchase in purchases]))
    
    # VIP
    df_purchases = pd.DataFrame(purchases, columns=['ID', 'Customer ID', 'Name', 'Amount', 'Payment Method', 'Date'])
    df_purchases['Date'] = pd.to_datetime(df_purchases['Date']).dt.strftime(date_format)
    vips = df_purchases.groupby(['Name']).agg({'Amount': 'sum'}).sort_values(by='Amount', ascending=False)
    
    col1.subheader(now)
    col1.write("---")
    col1.markdown(f"<p style='font-size:20px;font-weight:bold;'>매출 총액:  {format(total_sales, ',')} ₩</p>", unsafe_allow_html=True)
    col1.write(f"(매출: {format(total_purchase, ',')}₩ / 환불: {format(total_refund, ',')}₩ )")
    col1.write(f"<p style='font-size:20px;font-weight:bold;'>다녀간 손님 수: {format(len(names), ',')}명 </p>", unsafe_allow_html=True)
    if not vips.empty:
        col1.write(f"<p style='font-size:20px;font-weight:bold;'>VIP: {vips.iloc[0].name}  ( 구매 금액: {format(int(vips.iloc[0].get('Amount')), ',')} ₩ )", unsafe_allow_html=True)
    
    # 구매 내역
    col2.subheader("구매 내역")
    df_purchases = pd.DataFrame(purchases, columns=['ID', 'Customer ID', 'Name', 'Amount', 'Payment Method', 'Date'])
    df_purchases['Date'] = pd.to_datetime(df_purchases['Date']).dt.strftime(date_format)
    purchase_summary = df_purchases.groupby(['Date', 'Payment Method']).agg({'Amount': 'sum'}).reset_index()
    col2.dataframe(purchase_summary, height=400, width=600)
    
    # 환불 내역
    col2.subheader("환불 내역")
    df_refunds = pd.DataFrame(refunds, columns=['ID', 'Customer ID', 'Name', 'Amount', 'Date'])
    df_refunds['Date'] = pd.to_datetime(df_refunds['Date']).dt.strftime(date_format)
    refund_summary = df_refunds.groupby(['Date', 'Name']).agg({'Amount': 'sum'}).reset_index()
    col2.dataframe(refund_summary, height=400, width=600)
