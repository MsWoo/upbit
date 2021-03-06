import requests
import logging
import pandas as pd
import time 

server_url = 'https://api.upbit.com'
line_target_url = 'https://notify-api.line.me/api/notify'

def send_request(reqType, reqUrl, reqParam, reqHeader):
    try:
        err_sleep_time = 0.3
        while True:
            response = requests.request(reqType, reqUrl, params=reqParam, headers=reqHeader)

            if 'Remaining-Req' in response.headers:
                hearder_info = response.headers['Remaining-Req']
                start_idx = hearder_info.find("sec=")
                end_idx = len(hearder_info)
                remain_sec = hearder_info[int(start_idx):int(end_idx)].replace('sec=', '')

            else:
                logging.error("헤더 정보 이상")
                logging.error(response.headers)
                break

            if int(remain_sec) < 3:
                logging.debug("요청 가능회수 한도 도달! 남은횟수:" + str(remain_sec))
                time.sleep(err_sleep_time)
 
            if response.status_code == 200 or response.status_code == 201:
                break

            elif response.status_code == 429:
                logging.error("요청 가능회수 초과!:" + str(response.status_code))
                time.sleep(err_sleep_time)

            else:
                logging.error("기타 에러:" + str(response.status_code))
                logging.error(response.status_code)
                logging.error(response)
                break
 
            logging.info("[restRequest] 요청 재처리중...")
 
        return response

    except Exception:
        raise

def get_candle(target_item, tick_kind, inq_range):
    try:

        if tick_kind == "1" or tick_kind == "3" or tick_kind == "5" or tick_kind == "10" or tick_kind == "15" or tick_kind == "30" or tick_kind == "60" or tick_kind == "240":
            target_url = "minutes/" + tick_kind

        elif tick_kind == "D":
            target_url = "days"

        elif tick_kind == "W":
            target_url = "weeks"

        elif tick_kind == "M":
            target_url = "months"

        else:
            raise Exception("잘못된 틱 종류:" + str(tick_kind))
 
        logging.debug(target_url)

        querystring = {"market": target_item, "count": inq_range}
        res = send_request("GET", server_url + "/v1/candles/" + target_url, querystring, "")
        candle_data = res.json()
 
        logging.debug(candle_data)
 
        return candle_data

    except Exception:
        raise

def send_line_message(message, line_token):
    try:
        headers = {'Authorization': 'Bearer ' + line_token}
        data = {'message': message}
 
        response = requests.post(line_target_url, headers=headers, data=data)        
 
        return response

    except Exception:
        raise
		
def get_rsi(candle_data):
    try:
        df = pd.DataFrame(candle_data)
        df = df.reindex(index=df.index[::-1]).reset_index()
 
        df['close'] = df["trade_price"]
 
        # RSI 계산
        def rsi(ohlc: pd.DataFrame, period: int = 14):
            ohlc["close"] = ohlc["close"]
            delta = ohlc["close"].diff()
 
            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0
 
            _gain = up.ewm(com=(period - 1), min_periods=period).mean()
            _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
 
            RS = _gain / _loss
            return pd.Series(100 - (100 / (1 + RS)), name="RSI")
 
        rsi = round(rsi(df, 14).iloc[-1], 4)
        return rsi
 
    except Exception:
        raise
		
def get_macd(candle_data, loop_cnt):
    try:
        candle_datas = []
        macd_list = []

        for i in range(0, int(loop_cnt)):
            candle_datas.append(candle_data[i:int(len(candle_data))])
 
        df = pd.DataFrame(candle_datas[0])
        df = df.iloc[::-1]
        df = df['trade_price']

        exp1 = df.ewm(span=12, adjust=False).mean()
        exp2 = df.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        exp3 = macd.ewm(span=9, adjust=False).mean()
 
        for i in range(0, int(loop_cnt)):
            macd_list.append(
                {"type": "MACD", "DT": candle_datas[0][i]['candle_date_time_kst'], "MACD": round(macd[i], 4), "SIGNAL": round(exp3[i], 4),
                 "OCL": round(macd[i] - exp3[i], 4)})

        return macd_list

    except Exception:
        raise
		
def get_mfi(candle_data):
    try:
        mfi_list = []

        df = pd.DataFrame(candle_data)
        dfDt = df['candle_date_time_kst'].iloc[::-1]
 
        df['typical_price'] = (df['trade_price'] + df['high_price'] + df['low_price']) / 3
        df['money_flow'] = df['typical_price'] * df['candle_acc_trade_volume']
 
        positive_mf = 0
        negative_mf = 0
 
        for i in range(0, 14):
 
            if df["typical_price"][i] > df["typical_price"][i + 1]:
                positive_mf = positive_mf + df["money_flow"][i]
            elif df["typical_price"][i] < df["typical_price"][i + 1]:
                negative_mf = negative_mf + df["money_flow"][i]
 
        if negative_mf > 0:
            mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
        else:
            mfi = 100 - (100 / (1 + (positive_mf)))
 
        mfi_list.append({"type": "MFI", "DT": dfDt[0], "MFI": round(mfi, 4)})
 
        return mfi_list
		
    except Exception:
        raise
		
def get_bb(candle_data):
    try:
        bb_list = []

        df = pd.DataFrame(candle_data)
        dfDt = df['candle_date_time_kst'].iloc[::-1]
        df = df['trade_price'].iloc[::-1]
 
            # 표준편차(곱)
        unit = 2
 
        band1 = unit * numpy.std(df[len(df) - 20:len(df)])
        bb_center = numpy.mean(df[len(df) - 20:len(df)])
        band_high = bb_center + band1
        band_low = bb_center - band1
 
        bb_list.append({"type": "BB", "DT": dfDt[0], "BBH": round(band_high, 4), "BBM": round(bb_center, 4),
                        "BBL": round(band_low, 4)})
 
        return bb_list

    except Exception:
        raise
		
def get_williams(candle_data):
    try:
        williams_list = []
 
        df = pd.DataFrame(candle_data)
        dfDt = df['candle_date_time_kst'].iloc[::-1]
        df = df.iloc[:14]
 
        hh = numpy.max(df['high_price'])
        ll = numpy.min(df['low_price'])
        cp = df['trade_price'][0]
 
        w = (hh - cp) / (hh - ll) * -100
 
        williams_list.append(
            {"type": "WILLIAMS", "DT": dfDt[0], "HH": round(hh, 4), "LL": round(ll, 4), "CP": round(cp, 4),
            "W": round(w, 4)})
 
        return williams_list
 
    except Exception:
        raise

def get_cci(candle_data, loop_cnt):
    try:
        cci_list = []
 
        df = pd.DataFrame(candle_data)
        ordered_df = df.sort_values(by=['candle_date_time_kst'], ascending=[True])
 
        ordered_df['TP'] = (ordered_df['high_price'] + ordered_df['low_price'] + ordered_df['trade_price']) / 3
        ordered_df['SMA'] = ordered_df['TP'].rolling(window=20).mean()
        ordered_df['MAD'] = ordered_df['TP'].rolling(window=20).apply(lambda x: pd.Series(x).mad())
        ordered_df['CCI'] = (ordered_df['TP'] - ordered_df['SMA']) / (0.015 * ordered_df['MAD'])

        for i in range(0, loop_cnt):            
            cci_list.append({"type": "CCI", "DT": ordered_df['candle_date_time_kst'].loc[i], "CCI": round(ordered_df['CCI'].loc[i], 4)})
 
        return cci_list

    except Exception:
        raise