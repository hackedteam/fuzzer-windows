timeout 1
cd fontfuzzer
"C:\Program Files\Git\bin\sh.exe"  --login -i -c "git pull"
REM del agent1.db
REM python hostagent.py setup
python hostagent.py