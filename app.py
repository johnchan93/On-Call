import streamlit as st
from datetime import date, timedelta
import holidays
import pandas as pd

# Initialize Hong Kong holidays
hk_holidays = holidays.HK()

# Doctor lists
CALL_LIST_1 = ["YMC", "WT", "YY", "Nat", "Ting", "So"]
CALL_LIST_2 = ["JCY", "HW", "Kel", "HYL", "SC"]

# Initialize session state to preserve data between runs
if 'doctors' not in st.session_state:
    st.session_state.doctors = {
        "List1": {name: {"weekday": 0, "weekend": 0, "holiday": 0, "last_shift": None} for name in CALL_LIST_1},
        "List2": {name: {"weekday": 0, "weekend": 0, "holiday": 0, "last_shift": None} for name in CALL_LIST_2}
    }

def generate_calendar(year, month):
    start_date = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    end_date = date(year if next_month > month else year + 1, next_month, 1) - timedelta(days=1)
    
    calendar = []
    current_date = start_date
    while current_date <= end_date:
        day_type = "holiday" if current_date in hk_holidays else \
                   "weekend" if current_date.weekday() >= 5 else "weekday"
        calendar.append({"date": current_date, "type": day_type})
        current_date += timedelta(days=1)
    return calendar

def assign_shifts(calendar, doctor_list, list_name):
    schedule = []
    for day in calendar:
        eligible_doctors = [
            doc for doc in doctor_list
            if (st.session_state.doctors[list_name][doc]["last_shift"] is None) or 
               (day["date"] - st.session_state.doctors[list_name][doc]["last_shift"]).days > 1
        ]
        
        if not eligible_doctors:
            eligible_doctors = doctor_list  # Reset if all doctors need to be considered
            
        eligible_doctors.sort(key=lambda x: (
            st.session_state.doctors[list_name][x][day["type"]],
            st.session_state.doctors[list_name][x]["weekday"] + 
            st.session_state.doctors[list_name][x]["weekend"] +
            st.session_state.doctors[list_name][x]["holiday"]
        ))
        
        assigned_doctor = eligible_doctors[0]
        st.session_state.doctors[list_name][assigned_doctor][day["type"]] += 1
        st.session_state.doctors[list_name][assigned_doctor]["last_shift"] = day["date"]
        schedule.append((day["date"], assigned_doctor, day["type"]))
    return schedule

# Streamlit UI
st.title("🏥 Doctor On-Call Scheduler")

# Month selection
selected_month = st.date_input("Select month", date.today()).replace(day=1)
calendar = generate_calendar(selected_month.year, selected_month.month)

if st.button("Generate Schedule"):
    # Generate schedules for both lists
    schedule1 = assign_shifts(calendar, CALL_LIST_1, "List1")
    schedule2 = assign_shifts(calendar, CALL_LIST_2, "List2")
    
    # Display schedules
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1st Call List Schedule")
        for entry in schedule1:
            st.write(f"{entry[0].strftime('%a %d %b')}: {entry[1]} ({entry[2]})")
    
    with col2:
        st.subheader("2nd Call List Schedule")
        for entry in schedule2:
            st.write(f"{entry[0].strftime('%a %d %b')}: {entry[1]} ({entry[2]})")

    # Show statistics
    st.subheader("Doctor Statistics")
    stats = []
    for list_name in ["List1", "List2"]:
        for doctor, data in st.session_state.doctors[list_name].items():
            stats.append({
                "List": list_name,
                "Doctor": doctor,
                "Weekday Shifts": data["weekday"],
                "Weekend Shifts": data["weekend"],
                "Holiday Shifts": data["holiday"],
                "Total Shifts": data["weekday"] + data["weekend"] + data["holiday"]
            })
    
    df = pd.DataFrame(stats)
    st.dataframe(df.style.highlight_max(axis=0, color="#f5f5f5"))

# Reset system at beginning of month
if st.button("Reset System for New Month"):
    st.session_state.doctors = {
        "List1": {name: {"weekday": 0, "weekend": 0, "holiday": 0, "last_shift": None} for name in CALL_LIST_1},
        "List2": {name: {"weekday": 0, "weekend": 0, "holiday": 0, "last_shift": None} for name in CALL_LIST_2}
    }
    st.success("System reset for new month!")
