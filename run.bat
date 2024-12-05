@echo on
cd C:\Projects\radio_presenter_management
waitress-serve --host=0.0.0.0 --port=5000 app:app
