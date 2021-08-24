import datetime
from datetime import timezone
import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

def update_job(status, id_job):
  print(str(status) + " va " + str(id_job))
  """ update job status  """
  sql = """ UPDATE jobs_job
              SET status = %s
              WHERE id = %s"""
  db = None
  updated_rows = 0
  try:
      db = psycopg2.connect(host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
      cursor = db.cursor()
      cursor.execute(sql, (status, id_job))
      updated_rows = cursor.rowcount
      db.commit()
      cursor.close()
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)
  finally:
      if db is not None:
          db.close()

  return updated_rows

def get_jobs():
  db = None
  now_time = datetime.datetime.now().replace(tzinfo=None)
  try:
    db = psycopg2.connect(host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jobs_job ORDER BY id")
    row = cursor.fetchone()
    
    while row is not None:
      id_job = row[0]
      start_time = row[3]
      end_time = row[4]
      print("Start time: {0}, Time now: {1}, End time: {2}".format(start_time, now_time, end_time))
      if start_time <= now_time and now_time <= end_time:
        update_job(True, id_job)
      else:
        update_job(False, id_job)
      row = cursor.fetchone()
    cursor.close()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    if db is not None:
      db.close()  
  
if __name__ == '__main__':
  get_jobs()