import os,time,tempfile,statistics,json
os.environ['QT_QPA_PLATFORM']='offscreen'
from tests.test_processes import APP,spin_until
from naatik_next.processes import Task
with tempfile.TemporaryDirectory() as profile:
 os.environ['NAATIK_WINDOWS_PROFILE']=profile
 result={}
 for persistent in (False,True):
  task=Task(persistent=persistent); values=[]; errors=[]; answers=[]
  task.result.connect(answers.append);task.error.connect(errors.append)
  try:
   for i in range(8):
    start=time.perf_counter();task.start({'action':'lookup','term':'日本'})
    spin_until(lambda:len(answers)>i or bool(errors))
    assert not errors,errors
    values.append(round((time.perf_counter()-start)*1000,2))
   result['persistent' if persistent else 'one_shot']={'first_ms':values[0],'warm_median_ms':statistics.median(values[1:]),'samples_ms':values}
  finally:task.close()
 print(json.dumps(result,indent=2))
