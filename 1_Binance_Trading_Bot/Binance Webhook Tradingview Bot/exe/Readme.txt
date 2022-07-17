1. run ngrok.exe
2. use command 'ngrok.exe http 5000'
3. copy Forwarding to Webhook URL in edit alert on tradingview 
4. 'http://e455-49-228-196-189.ngrok.io'+'/tradingview'
5. add message order command '{"cmd": "buy","amount":"0.001","symbol": "BTCUSDT","passphrase": "Test1234"}'
6. run TradingviewBotFull.exe