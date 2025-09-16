from app.dashboard.db_helper import get_dashboard_data_from_db



def get_dashboard_data(db):
    dashboard_data_response = get_dashboard_data_from_db(db)
    return dashboard_data_response