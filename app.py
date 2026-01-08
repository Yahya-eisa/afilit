import streamlit as st
import pandas as pd
import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

# ---------- Google Sheets Setup ----------
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_google_sheets_client():
    """Initialize Google Sheets client"""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def load_orders_from_sheet(sheet_name="Orders Database"):
    """Load existing orders from Google Sheets"""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.sheet1
        
        # Get all records
        data = worksheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            return df
        else:
            # Create empty dataframe with columns
            columns = [
                'كود الاوردر', 'اسم العميل', 'رقم الموبايل', 'المنطقة', 'العنوان',
                'حالة الاوردر', 'اسم الصنف', 'اللون', 'المقاس', 'الكمية',
                'الملاحظات', 'الإجمالي مع الشحن', 'تاريخ التسجيل'
            ]
            return pd.DataFrame(columns=columns)
    except Exception as e:
        st.error(f"خطأ في التحميل: {str(e)}")
        columns = [
            'كود الاوردر', 'اسم العميل', 'رقم الموبايل', 'المنطقة', 'العنوان',
            'حالة الاوردر', 'اسم الصنف', 'اللون', 'المقاس', 'الكمية',
            'الملاحظات', 'الإجمالي مع الشحن', 'تاريخ التسجيل'
        ]
        return pd.DataFrame(columns=columns)

def save_order_to_sheet(order_data, sheet_name="Orders Database"):
    """Save new order to Google Sheets"""
    try:
        client = get_google_sheets_client()
        
        try:
            spreadsheet = client.open(sheet_name)
        except:
            # Create new spreadsheet if doesn't exist
            spreadsheet = client.create(sheet_name)
            spreadsheet.share('', perm_type='anyone', role='writer')
        
        worksheet = spreadsheet.sheet1
        
        # Check if headers exist
        existing_data = worksheet.get_all_values()
        
        if not existing_data:
            # Add headers
            headers = [
                'كود الاوردر', 'اسم العميل', 'رقم الموبايل', 'المنطقة', 'العنوان',
                'حالة الاوردر', 'اسم الصنف', 'اللون', 'المقاس', 'الكمية',
                'الملاحظات', 'الإجمالي مع الشحن', 'تاريخ التسجيل'
            ]
            worksheet.append_row(headers)
        
        # Append new order
        row_data = [
            order_data.get('كود الاوردر', ''),
            order_data.get('اسم العميل', ''),
            order_data.get('رقم الموبايل', ''),
            order_data.get('المنطقة', ''),
            order_data.get('العنوان', ''),
            order_data.get('حالة الاوردر', ''),
            order_data.get('اسم الصنف', ''),
            order_data.get('اللون', ''),
            order_data.get('المقاس', ''),
            order_data.get('الكمية', ''),
            order_data.get('الملاحظات', ''),
            order_data.get('الإجمالي مع الشحن', ''),
            order_data.get('تاريخ التسجيل', '')
        ]
        
        worksheet.append_row(row_data)
        return True, spreadsheet.url
    except Exception as e:
        return False, str(e)

# ---------- Main App ----------
st.set_page_config(page_title="📝 تسجيل الأوردرات", layout="wide")
st.title("📝 نظام تسجيل الأوردرات - Affiliate Dashboard")

# Initialize session state
if 'orders_df' not in st.session_state:
    st.session_state.orders_df = None
    st.session_state.sheet_url = None

# Load existing data from Google Sheets
if st.session_state.orders_df is None:
    with st.spinner("🔄 جاري تحميل البيانات من Google Sheets..."):
        df = load_orders_from_sheet()
        st.session_state.orders_df = df
        
        if len(df) > 0:
            st.success(f"✅ تم تحميل {len(df)} أوردر من Google Sheets")
        else:
            st.info("📝 جاهز لإضافة أوردرات جديدة")

# Display statistics in header
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📊 إجمالي الأوردرات", len(st.session_state.orders_df))

with col2:
    if len(st.session_state.orders_df) > 0 and 'الإجمالي مع الشحن' in st.session_state.orders_df.columns:
        total_revenue = pd.to_numeric(st.session_state.orders_df['الإجمالي مع الشحن'], errors='coerce').sum()
        st.metric("💰 إجمالي المبيعات", f"{total_revenue:.2f} KD")
    else:
        st.metric("💰 إجمالي المبيعات", "0.00 KD")

with col3:
    if st.session_state.sheet_url:
        st.link_button("🔗 فتح Google Sheet", st.session_state.sheet_url)
    else:
        st.info("سيتم إنشاء الشيت مع أول أوردر")

# Form for new order
st.markdown("---")
st.subheader("➕ إضافة أوردر جديد")

with st.form("new_order_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        order_code = st.text_input("كود الاوردر *", placeholder="مثال: ORD-001")
        customer_name = st.text_input("اسم العميل *", placeholder="اسم العميل")
        phone = st.text_input("رقم الموبايل *", placeholder="مثال: 96512345678")
        area = st.text_input("المنطقة *", placeholder="مثال: حولي")
    
    with col2:
        address = st.text_area("العنوان", placeholder="العنوان التفصيلي", height=100)
        status = st.selectbox("حالة الاوردر *", 
                             ["تم التأكيد", "قيد التجهيز", "تم الشحن", "تم التسليم", "ملغي"],
                             index=0)
        product_name = st.text_input("اسم الصنف *", placeholder="اسم المنتج")
    
    with col3:
        color = st.text_input("اللون", placeholder="مثال: أحمر")
        size = st.text_input("المقاس", placeholder="مثال: L")
        quantity = st.number_input("الكمية *", min_value=1, value=1, step=1)
        notes = st.text_area("الملاحظات", placeholder="أي ملاحظات إضافية", height=100)
        total = st.number_input("الإجمالي مع الشحن *", min_value=0.0, value=0.0, step=0.5, format="%.2f")
    
    col_submit1, col_submit2 = st.columns([3, 1])
    with col_submit1:
        submitted = st.form_submit_button("💾 حفظ الأوردر", use_container_width=True, type="primary")
    with col_submit2:
        refresh = st.form_submit_button("🔄 تحديث", use_container_width=True)
    
    if refresh:
        st.session_state.orders_df = None
        st.rerun()
    
    if submitted:
        # Validation
        if not order_code or not customer_name or not phone or not area or not product_name:
            st.error("⚠️ يرجى ملء جميع الحقول المطلوبة (*)")
        else:
            # Get current timestamp
            tz = pytz.timezone('Africa/Cairo')
            timestamp = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            
            # Create new order
            new_order = {
                'كود الاوردر': order_code,
                'اسم العميل': customer_name,
                'رقم الموبايل': phone,
                'المنطقة': area,
                'العنوان': address,
                'حالة الاوردر': status,
                'اسم الصنف': product_name,
                'اللون': color,
                'المقاس': size,
                'الكمية': quantity,
                'الملاحظات': notes,
                'الإجمالي مع الشحن': total,
                'تاريخ التسجيل': timestamp
            }
            
            # Save to Google Sheets
            with st.spinner("💾 جاري الحفظ على Google Sheets..."):
                success, result = save_order_to_sheet(new_order)
                
                if success:
                    st.session_state.sheet_url = result
                    st.success(f"✅ تم حفظ الأوردر #{order_code} بنجاح!")
                    st.balloons()
                    
                    # Reload data
                    st.session_state.orders_df = None
                    st.rerun()
                else:
                    st.error(f"❌ فشل الحفظ: {result}")

# Display recent orders
st.markdown("---")
st.subheader("📋 آخر 10 أوردرات")

if len(st.session_state.orders_df) > 0:
    # Sort by date if column exists
    if 'تاريخ التسجيل' in st.session_state.orders_df.columns:
        recent_orders = st.session_state.orders_df.tail(10).sort_values('تاريخ التسجيل', ascending=False)
    else:
        recent_orders = st.session_state.orders_df.tail(10)
    
    st.dataframe(
        recent_orders, 
        use_container_width=True, 
        hide_index=True,
        height=400
    )
    
    # Search functionality
    st.markdown("---")
    st.subheader("🔍 البحث في الأوردرات")
    
    search_col1, search_col2 = st.columns(2)
    
    with search_col1:
        search_term = st.text_input("ابحث عن أوردر (كود، اسم، موبايل)", placeholder="اكتب للبحث...")
    
    if search_term:
        search_results = st.session_state.orders_df[
            st.session_state.orders_df.astype(str).apply(
                lambda row: row.str.contains(search_term, case=False, na=False).any(), 
                axis=1
            )
        ]
        
        st.write(f"نتائج البحث: {len(search_results)} أوردر")
        st.dataframe(search_results, use_container_width=True, hide_index=True)
else:
    st.info("💡 لا توجد أوردرات مسجلة حتى الآن. ابدأ بإضافة أول أوردر!")

# Statistics by area
if len(st.session_state.orders_df) > 0:
    st.markdown("---")
    st.subheader("📊 إحصائيات حسب المنطقة")
    
    if 'المنطقة' in st.session_state.orders_df.columns:
        area_stats = st.session_state.orders_df['المنطقة'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**عدد الأوردرات لكل منطقة:**")
            st.dataframe(area_stats.reset_index().rename(columns={'index': 'المنطقة', 'المنطقة': 'العدد'}), 
                        use_container_width=True, hide_index=True)
        
        with col2:
            if 'حالة الاوردر' in st.session_state.orders_df.columns:
                st.write("**إحصائيات حسب الحالة:**")
                status_stats = st.session_state.orders_df['حالة الاوردر'].value_counts()
                st.dataframe(status_stats.reset_index().rename(columns={'index': 'الحالة', 'حالة الاوردر': 'العدد'}), 
                            use_container_width=True, hide_index=True)
