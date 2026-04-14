

import streamlit as st
import plotly.graph_objects as go
from google import genai
from google.genai import types
from pydantic import BaseModel
import json
import os
import ssl
import urllib3

# --- 🚀 שלב 1: עקיפת SSL ---
orig_create_default_context = ssl.create_default_context
def patched_create_default_context(*args, **kwargs):
    context = orig_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

ssl.create_default_context = patched_create_default_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['PYTHONHTTPSVERIFY'] = '0'

# --- 📚 שלב 2: הגדרת סכמת נתונים לחיתום מתקדם ---
class ComprehensiveBuildingFacts(BaseModel):
    unoccupied_signs: bool         
    wall_moisture_detected: bool   
    severe_neglect: bool           
    overcrowding_signs: bool       
    large_pergola: bool            
    pool_or_jacuzzi: bool          
    split_apartment: bool          
    business_activity: bool        
    expensive_storage: bool        
    is_luxury_apartment: bool      
    estimated_age_years: int       
    estimated_area_sqm: int        
    hazard_description: str        

# --- 🎯 שלב 3: פונקציית ציון וניתוח פערים ---
def calculate_risk_score(facts, errors):
    score = 100
    
    if facts['unoccupied_signs']: score -= 25
    if facts['wall_moisture_detected']: score -= 20
    if facts['severe_neglect']: score -= 30
    if facts['overcrowding_signs']: score -= 15
    if facts['split_apartment']: score -= 25
    if facts['business_activity']: score -= 20
    
    score -= (len(errors) * 15)
    final_score = max(0, score)
    
    if final_score >= 85:
        return final_score, "אישור אוטומטי (Green Light)", "success"
    elif final_score >= 60:
        return final_score, "דרושה בדיקת חתם אנושי / עדכון תעריף", "warning"
    else:
        return final_score, "דחייה - סיכון גבוה לחיתום (Reject)", "error"

def display_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "ציון חיתום מסכם", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 59], 'color': "#ff4b4b"},
                {'range': [60, 84], 'color': "#ffa421"},
                {'range': [85, 100], 'color': "#21c354"}
            ],
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# --- הגדרות דף ---
st.set_page_config(page_title="מנוע חיתום AI", page_icon="🏢", layout="wide")
st.title("🏢 מנוע חיתום AI: זיהוי סיכונים רב-תמונתי")


# התחברות ל-API
# client = genai.Client(api_key="AIzaSyCAMU7B-_9t86_XaFfIAkgoC-1Bg7vAr_Y")
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# --- ממשק משתמש: נתוני פוליסה ---
st.sidebar.header("📋 נתוני הפוליסה (הצהרת לקוח)")
policy_area = st.sidebar.number_input("שטח הדירה בפוליסה (מ\"ר):", min_value=10, value=100)
policy_age = st.sidebar.number_input("גיל הדירה בפוליסה (בשנים):", min_value=0, value=5)
declaration = st.sidebar.text_area("הערות הלקוח:", "דירה סטנדרטית, משמשת למגורים בלבד.")

model_choice = st.sidebar.selectbox("בחר מודל AI:", [
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-latest", 
    "gemini-3.1-pro-preview"
])

# --- העלאת תמונות מרובות ---
st.write("📸 **העלה תמונות של הנכס:** (כניסה, מבחוץ, סלון, מטבח, חדרי שינה, גינה/מרפסת, מחסן)")
uploaded_files = st.file_uploader("בחר תמונות (ניתן לבחור מספר קבצים יחד)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

if uploaded_files and st.button("בצע ניתוח חיתום מקיף 🚀"):
    
    # הצגת התמונות בגלריה קטנה (Grid)
    st.write("🖼️ **התמונות שהתקבלו:**")
    cols = st.columns(min(len(uploaded_files), 5)) # תצוגה של עד 5 עמודות בשורה
    for i, file in enumerate(uploaded_files):
        cols[i % 5].image(file, use_container_width=True)
    
    st.divider()
    
    with st.spinner("ה-AI סורק את כלל התמונות ומגבש פרופיל חיתום..."):
        
        # בניית הפקודה והנחיית המודל שהוא מסתכל על אוסף תמונות של אותו נכס
        prompt = """
        You are an expert insurance underwriter. You are provided with a collection of images belonging to a SINGLE property. 
        The images may include the entrance, exterior, interior rooms, garden, and storage.
        Analyze the property as a whole based on ALL provided images. If a feature (like a pool or pergola) is not visible in any image, assume it is false.
        Identify the following and return the data in JSON:
        1. unoccupied_signs: Is it completely empty or abandoned?
        2. wall_moisture_detected: Any signs of mold or water damage in any room?
        3. severe_neglect: Is the property overall extremely worn out or neglected?
        4. overcrowding_signs: Signs of unusual crowding (e.g., many beds, clutter)?
        5. large_pergola: Is there a large outdoor pergola visible?
        6. pool_or_jacuzzi: Is there a swimming pool or jacuzzi visible?
        7. split_apartment: Signs the unit is divided (multiple front doors, extra kitchens)?
        8. business_activity: Signs of a business (commercial equipment, waiting area)?
        9. expensive_storage: Are there high-value items stored in what looks like a storage room?
        10. is_luxury_apartment: High standard of living/luxury finishes overall?
        11. estimated_age_years: Visually estimate the age of the building in years (integer).
        12. estimated_area_sqm: Estimate the total visible area in square meters (integer).
        13. hazard_description: Brief summary of found risks across all images (in Hebrew).
        """
        
        # הכנת מערך החלקים (Parts) שיישלח ל-API
        request_parts = [types.Part.from_text(text=prompt)]
        for file in uploaded_files:
            file_bytes = file.getvalue()
            request_parts.append(types.Part.from_bytes(data=file_bytes, mime_type=file.type))
        
        try:
            response = client.models.generate_content(
                model=model_choice,
                contents=[
                    types.Content(
                        role="user",
                        parts=request_parts
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ComprehensiveBuildingFacts,
                ),
            )
            
            facts = json.loads(response.text)
            
            # --- תצוגת ממצאים מבוססת התראות ---
            st.subheader("🔍 דוח פרמטרים מסכם (מבוסס על כל התמונות):")
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.write("**מצב ואכלוס:**")
                if facts['unoccupied_signs']: st.error("🚨 הנכס נראה ריק/לא מאויש")
                if facts['severe_neglect']: st.error("🚨 עדות להזנחה ובלאי משמעותי")
                if facts['wall_moisture_detected']: st.warning("⚠️ זוהתה רטיבות באחת התמונות")
                if facts['overcrowding_signs']: st.warning("⚠️ חשד לאכלוס חריג")
            
            with c2:
                st.write("**חבויות ושימוש:**")
                if facts['split_apartment']: st.error("🚨 חשד לדירה מפוצלת")
                if facts['business_activity']: st.error("🚨 חשד לקיום עסק בדירה")
                if facts['large_pergola']: st.info("ℹ️ זוהתה פרגולה גדולה")
                if facts['pool_or_jacuzzi']: st.warning("⚠️ זוהה ג'קוזי / בריכה")
                if facts['expensive_storage']: st.info("ℹ️ תכולה יקרה במחסן")
                if facts['is_luxury_apartment']: st.info("💎 הנכס סווג כדירת יוקרה")

            with c3:
                st.write("**הערכות AI (מול פוליסה):**")
                st.write(f"- שטח נצפה מצטבר: ~{facts['estimated_area_sqm']} מ\"ר")
                st.write(f"- גיל מבנה מוערך: ~{facts['estimated_age_years']} שנים")
                
            st.write(f"**תיאור AI:** {facts['hazard_description']}")

            # --- לוגיקת פערים והצלבה מול נתוני פוליסה ---
            errors = []
            
            if facts['estimated_area_sqm'] > (policy_area * 1.2):
                errors.append(f"❌ **פער בשטח:** השטח המוערך (~{facts['estimated_area_sqm']} מ\"ר) גדול ביותר מ-20% מהצהרת הפוליסה ({policy_area} מ\"ר).")
            
            if abs(facts['estimated_age_years'] - policy_age) > 20:
                errors.append(f"❌ **פער בגיל המבנה:** הפוליסה מציינת {policy_age} שנים, אך הנכס מוערך כבן {facts['estimated_age_years']} שנים.")

            if facts['business_activity'] and "עסק" not in declaration:
                errors.append("❌ **פער שימוש:** זוהה עסק בדירה ללא הצהרה מתאימה.")

            # --- הצגת ציון והחלטה סופית ---
            st.divider()
            st.subheader("⚖️ החלטת חיתום משוקללת (לכלל הנכס):")
            
            score, recommendation, alert_type = calculate_risk_score(facts, errors)
            
            col_score, col_dec = st.columns([1, 1])
            
            with col_score:
                display_gauge_chart(score)
                
            with col_dec:
                st.write("### פערי פוליסה שזוהו:")
                if errors:
                    for err in errors:
                        st.write(err)
                else:
                    st.write("✅ התמונות תואמות לפרטי הפוליסה ללא פערים מהותיים.")
                    
                st.write("### המלצת מערכת:")
                if alert_type == "success":
                    st.success(recommendation)
                elif alert_type == "warning":
                    st.warning(recommendation)
                else:
                    st.error(recommendation)

        except Exception as e:
            st.error(f"שגיאה בניתוח: {e}")