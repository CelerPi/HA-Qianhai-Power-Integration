from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any

from aiohttp import ClientError, ClientSession

from .crypto import encode_request_payload, rsa_encrypt_path

SERVICE_INVOKE_PATH = "/wechatWeb/wx/serviceInvoke"

REQUEST_API = {
    "rcvblList": "/wechat/biArrearsRecord/rcvblList",
    "queryArrearageDetail": "/wechat/biArrearsRecord/rcvblDetail",
    "queryRcvblHistoryl": "/wechat/biArrearsRecord/rcvblHistory",
}


class QianhaiPowerApiError(Exception):
    """Raised when Qianhai Power cannot return usable data."""


@dataclass(frozen=True)
class QianhaiBill:
    amount_month: str | None = None
    user_no: str | None = None
    user_name: str | None = None
    address: str | None = None
    money: float | None = None
    power: float | None = None
    owe: float | None = None
    lock_owe: float | None = None
    total_fee: float | None = None
    owe_flag: str | None = None
    elec_cust_no: str | None = None
    ele_user_category: str | None = None
    is_electricity_bill: str | None = None
    metering_point_no: str | None = None
    work_order_no: str | None = None
    receivable_account_sn: str | None = None
    electricity_sort: str | None = None
    price: str | None = None
    last_read_date: str | None = None
    current_read_date: str | None = None
    electricity_fee: float | None = None
    base_fee: float | None = None
    additional_fee: float | None = None
    power_adjust_fee: float | None = None
    refund_fee: float | None = None
    reduction_fee: float | None = None
    previous_meter_reading: float | None = None
    current_meter_reading: float | None = None
    meter_multiplier: float | None = None
    meter_asset_no: str | None = None
    meter_read_type: str | None = None
    owe_status: str | None = None
    step1_power: float | None = None
    step1_fee: float | None = None
    step1_price: float | None = None
    step1_name: str | None = None
    step1_percent: str | None = None
    step2_power: float | None = None
    step2_fee: float | None = None
    step2_price: float | None = None
    step2_name: str | None = None
    step2_percent: str | None = None
    step3_power: float | None = None
    step3_fee: float | None = None
    step3_price: float | None = None
    step3_name: str | None = None
    step3_percent: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QianhaiPowerData:
    latest_bill_amount: float | None = None
    latest_bill_usage: float | None = None
    latest_bill_month: str | None = None
    user_no: str | None = None
    user_name: str | None = None
    address: str | None = None
    bill_count: int = 0
    latest_bill: QianhaiBill | None = None
    bills: tuple[QianhaiBill, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)
    raw_top_keys: tuple[str, ...] = ()
    raw_data_keys: tuple[str, ...] = ()
    result_code: str | None = None
    result_message: str | None = None


class QianhaiPowerApiClient:
    def __init__(
        self,
        session: ClientSession,
        *,
        base_url: str,
        open_id: str,
        settle_acct_no: str,
        user_no: str | None,
        pay_type: str,
        token: str | None,
        jsessionid: str | None,
        months: int,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._open_id = open_id
        self._settle_acct_no = settle_acct_no
        self._user_no = user_no
        self._pay_type = pay_type
        self._token = token or ""
        self._jsessionid = jsessionid
        self._months = months

    async def async_fetch(self) -> QianhaiPowerData:
        today = date.today()
        ym_to = f"{today.year}{today.month:02d}"
        start_year = today.year
        start_month = today.month - self._months + 1
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        ym_from = f"{start_year}{start_month:02d}"

        payload = {
            "payType": self._pay_type,
            "settleAcctNo": self._settle_acct_no,
            "amtYmFrom": ym_from,
            "amtYmTo": ym_to,
            "pageNo": "1",
            "pageNum": "10",
        }
        response = await self._invoke("rcvblList", payload)
        bills = _extract_bills(response)
        latest = _latest_bill(bills)
        if latest and latest.user_no and latest.amount_month:
            detail_response = await self._invoke(
                "queryArrearageDetail",
                {
                    "payType": self._pay_type,
                    "userNo": latest.user_no,
                    "amtYm": latest.amount_month,
                },
            )
            latest = _merge_bill_detail(latest, detail_response)
        result = response.get("result") if isinstance(response.get("result"), dict) else {}

        return QianhaiPowerData(
            latest_bill_amount=latest.money if latest else None,
            latest_bill_usage=latest.power if latest else None,
            latest_bill_month=latest.amount_month if latest else None,
            user_no=latest.user_no if latest else self._user_no,
            user_name=latest.user_name if latest else None,
            address=latest.address if latest else None,
            bill_count=len(bills),
            latest_bill=latest,
            bills=tuple(_replace_latest_bill(bills, latest)),
            raw=response,
            raw_top_keys=tuple(response.keys()),
            raw_data_keys=tuple(response.get("data", {}).keys())
            if isinstance(response.get("data"), dict)
            else (),
            result_code=str(result.get("rslt")) if result.get("rslt") is not None else None,
            result_message=result.get("rsltinfo") or result.get("message"),
        )

    async def _invoke(self, service_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if service_name not in REQUEST_API:
            raise QianhaiPowerApiError(f"Unknown service: {service_name}")

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": self._base_url,
            "Referer": f"{self._base_url}/wechat/",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
                "MicroMessenger/8.0.74 NetType/WIFI Language/zh_CN"
            ),
            "token": self._token,
            "bindingNo": self._open_id,
            "hyServiceName": service_name,
            "hyRequestUrl": rsa_encrypt_path(REQUEST_API[service_name]),
        }
        cookies = {"openId": self._open_id}
        if self._jsessionid:
            cookies["JSESSIONID"] = self._jsessionid

        try:
            async with self._session.post(
                f"{self._base_url}{SERVICE_INVOKE_PATH}",
                headers=headers,
                cookies=cookies,
                json=encode_request_payload(payload),
                timeout=30,
            ) as response:
                if response.status >= 400:
                    raise QianhaiPowerApiError(f"HTTP {response.status}")
                data = await response.json(content_type=None)
        except ClientError as err:
            raise QianhaiPowerApiError("Request failed") from err
        except TimeoutError as err:
            raise QianhaiPowerApiError("Request timed out") from err
        except ValueError as err:
            raise QianhaiPowerApiError("Response is not JSON") from err

        if not isinstance(data, dict):
            raise QianhaiPowerApiError("Response JSON is not an object")

        data = _unwrap_response(data)
        result = data.get("result")
        if isinstance(result, dict) and str(result.get("rslt")) != "0":
            message = result.get("rsltinfo") or result.get("message") or result
            raise QianhaiPowerApiError(f"Service returned error: {message}")

        return data


def _unwrap_response(response: dict[str, Any]) -> dict[str, Any]:
    content = response.get("content")
    if isinstance(content, dict):
        return content
    data = response.get("data")
    if isinstance(data, dict) and isinstance(data.get("content"), dict):
        return data["content"]
    return response


def _extract_bills(response: dict[str, Any]) -> list[QianhaiBill]:
    candidates = (
        "arrearInfo",
        "rcvblList",
        "arrearInfoList",
        "arrearageList",
        "list",
        "rows",
        "records",
    )
    rows: Any = None
    for key in candidates:
        if isinstance(response.get(key), list):
            rows = response[key]
            break
    if rows is None and isinstance(response.get("data"), dict):
        for key in candidates:
            if isinstance(response["data"].get(key), list):
                rows = response["data"][key]
                break
    if rows is None:
        rows = _top_level_bill_rows(response)

    top_level_bill_data = _top_level_bill_data(response)
    bills = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row = {**row, **top_level_bill_data}
        bills.append(_bill_from_row(row))
    return bills


def _bill_from_row(row: dict[str, Any]) -> QianhaiBill:
    return QianhaiBill(
        amount_month=_first_str(row, "amtYm", "mon", "amountMonth", "ym"),
        user_no=_first_str(row, "userNo", "consNo", "elecCustNo"),
        user_name=_first_str(row, "userName", "consName"),
        address=_first_str(row, "address", "elecAddr", "addr"),
        money=_first_float(
            row,
            "money",
            "receAmt",
            "rcvblAmt",
            "amt",
            "totalFee",
            "owe",
            "lockOwe",
        ),
        power=_first_float(row, "power", "billPq", "pq", "totalPq"),
        owe=_first_float(row, "owe"),
        lock_owe=_first_float(row, "lockOwe"),
        total_fee=_first_float(row, "totalFee"),
        owe_flag=_first_str(row, "oweFlag"),
        elec_cust_no=_first_str(row, "elecCustNo"),
        ele_user_category=_first_str(row, "eleUserCategory"),
        is_electricity_bill=_first_str(row, "isElectricityBill"),
        owe_status=_first_str(row, "oweStatus"),
        raw=row,
    )


def _merge_bill_detail(bill: QianhaiBill, response: dict[str, Any]) -> QianhaiBill:
    detail_row = _extract_first_object(response, "arrearDetailInfo", "detail", "data")
    if detail_row is None:
        detail_row = {}

    ca_read = _extract_first_object(detail_row, "caReadInfos", "readInfos")
    if ca_read is None:
        ca_read = {}

    steps = _extract_object_list(detail_row, "stepInfos")
    step_values: dict[str, float | None] = {}
    step_text_values: dict[str, str | None] = {}
    for index in range(3):
        step = steps[index] if index < len(steps) else {}
        step_no = index + 1
        step_values[f"step{step_no}_power"] = _first_float(step, "totalPq", "power", "pq")
        step_values[f"step{step_no}_fee"] = _first_float(step, "totalAmt", "money", "amt")
        step_values[f"step{step_no}_price"] = _first_float(step, "prc", "price")
        step_text_values[f"step{step_no}_name"] = _first_str(step, "stepSort")
        step_text_values[f"step{step_no}_percent"] = _first_str(step, "percent")

    raw = {**bill.raw, **detail_row}
    return replace(
        bill,
        money=_coalesce(
            _first_float(detail_row, "money", "receAmt", "rcvblAmt", "amt"),
            bill.money,
        ),
        power=_coalesce(_first_float(detail_row, "power", "totalPq", "billPq"), bill.power),
        price=_coalesce(_first_str(detail_row, "price", "priceName"), bill.price),
        electricity_sort=_first_str(detail_row, "elecSort"),
        last_read_date=_first_str(detail_row, "ltMrDate"),
        current_read_date=_first_str(detail_row, "readDate"),
        metering_point_no=_first_str(detail_row, "mpNo"),
        work_order_no=_first_str(detail_row, "woNo"),
        receivable_account_sn=_first_str(detail_row, "rcvblAcctSn"),
        is_electricity_bill=_coalesce(
            _bill_type_from_owe_status(_first_str(detail_row, "oweStatus")),
            bill.is_electricity_bill,
        ),
        owe_status=_coalesce(_first_str(detail_row, "oweStatus"), bill.owe_status),
        total_fee=_coalesce(
            _first_float(detail_row, "receAmt", "money"),
            bill.total_fee,
            bill.money,
        ),
        electricity_fee=_first_float(detail_row, "pqAmt"),
        base_fee=_first_float(detail_row, "baseAmt"),
        additional_fee=_first_float(detail_row, "plusAmt"),
        power_adjust_fee=_first_float(detail_row, "pfAmt"),
        refund_fee=_first_float(detail_row, "totalRsAmt"),
        reduction_fee=_first_float(detail_row, "reduce"),
        previous_meter_reading=_first_float(ca_read, "ltMeterData"),
        current_meter_reading=_first_float(ca_read, "ttMeterNum"),
        meter_multiplier=_first_float(ca_read, "totalFactor"),
        meter_asset_no=_first_str(ca_read, "assetsNo"),
        meter_read_type=_first_str(ca_read, "readType"),
        step1_power=step_values["step1_power"],
        step1_fee=step_values["step1_fee"],
        step1_price=step_values["step1_price"],
        step1_name=step_text_values["step1_name"],
        step1_percent=step_text_values["step1_percent"],
        step2_power=step_values["step2_power"],
        step2_fee=step_values["step2_fee"],
        step2_price=step_values["step2_price"],
        step2_name=step_text_values["step2_name"],
        step2_percent=step_text_values["step2_percent"],
        step3_power=step_values["step3_power"],
        step3_fee=step_values["step3_fee"],
        step3_price=step_values["step3_price"],
        step3_name=step_text_values["step3_name"],
        step3_percent=step_text_values["step3_percent"],
        raw=raw,
    )


def _top_level_bill_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    row = _top_level_bill_data(response)
    if not row:
        return []
    return [row]


def _top_level_bill_data(response: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "totalFee",
        "owe",
        "lockOwe",
        "oweFlag",
        "amtYm",
        "elecCustNo",
        "eleUserCategory",
        "isElectricityBill",
        "userNo",
        "userName",
        "address",
    )
    return {
        key: response[key]
        for key in keys
        if response.get(key) not in (None, "")
    }


def _latest_bill(bills: list[QianhaiBill]) -> QianhaiBill | None:
    if not bills:
        return None
    return sorted(bills, key=lambda bill: bill.amount_month or "", reverse=True)[0]


def _replace_latest_bill(
    bills: list[QianhaiBill],
    latest: QianhaiBill | None,
) -> list[QianhaiBill]:
    if latest is None:
        return bills
    return [
        latest
        if bill.amount_month == latest.amount_month and bill.user_no == latest.user_no
        else bill
        for bill in bills
    ]


def _extract_first_object(
    source: dict[str, Any],
    *keys: str,
) -> dict[str, Any] | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
        if isinstance(value, dict):
            return value
    return None


def _extract_object_list(source: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = source.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _first_str(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return _decode_base64_string(value)
    return None


def _first_float(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            decoded = _decode_base64_string(value)
            try:
                return float(decoded)
            except (TypeError, ValueError):
                continue
    return None


def _decode_base64_string(value: Any) -> str:
    text = str(value)
    if not text or len(text) % 4 != 0:
        return text
    try:
        decoded_bytes = base64.b64decode(text, validate=True)
        decoded = decoded_bytes.decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return text
    if not decoded:
        return text
    return decoded


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _bill_type_from_owe_status(owe_status: str | None) -> str | None:
    if owe_status == "1":
        return "已缴纳电费"
    if owe_status == "0":
        return "应收电费"
    return None
