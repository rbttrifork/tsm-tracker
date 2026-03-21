' Silent TSM cloud push
Set shell = CreateObject("WScript.Shell")
shell.Environment("Process")("TSM_PUSH_API_KEY") = "TQoc8Z2x1JRqzMc7KsrTtoLAdQlwDs9LemdvTsQ3Aqk"
shell.Environment("Process")("TSM_CLOUD_URL") = "https://web-production-95183.up.railway.app"
shell.CurrentDirectory = "D:\Projects\tsm-tracker"
shell.Run "pythonw pusher.py", 0, False
