# run_pipeline.py
import os, time
start=time.time()
os.system("python 1_raw_load.py")
os.system("python 2_staging_clean.py")
os.system("python 3_attendance_daily.py")
os.system("python 4_warehouse_model.py")
os.system("python fix_final.py")
os.system("python 5_analytics_all10.py")
os.system("python 6_dq_checks.py")
print(f"\n🎉 Full Pipeline Done in {time.time()-start:.1f} sec!")