# from datetime import datetime, timedelta
#
# from apscheduler.schedulers.background import BackgroundScheduler
# from google.cloud.firestore_v1 import FieldFilter
#
# from firebase import db
#
#
# def test_job():
#     print('I am working...')
#
#
# def delete_old_records():
#     weeks = 2
#
#     # Calculate the timestamp for records older than 2 weeks
#     cutoff_time = datetime.utcnow() - timedelta(weeks=weeks)
#     logs_ref = db.collection("show_log")
#     query = logs_ref.where(filter=FieldFilter("created_at", "<", cutoff_time))
#     docs = query.stream()
#
#     deleted_count = 0
#     # Delete documents
#     for doc in docs:
#         doc.reference.delete()
#         deleted_count += 1
#         # print(f"{doc.id} => {doc.to_dict()}")
#
#     print(f"Deleted {deleted_count} records older than {weeks} weeks from the 'logs' collection.")
#
#
# # scheduler = BackgroundScheduler()
# # scheduler.add_job(delete_old_records, 'interval', weeks=4)
