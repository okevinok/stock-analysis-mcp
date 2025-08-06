"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getStockData = getStockData;
exports.getStockAlerts = getStockAlerts;
var axios_1 = require("axios");
var dotenv_1 = require("dotenv");
dotenv_1.default.config();
var API_KEY = process.env.ALPHA_VANTAGE_API_KEY;
var BASE_URL = 'https://www.alphavantage.co/query';
if (!API_KEY) {
    console.error('Alpha Vantage API key not found. Please set ALPHA_VANTAGE_API_KEY in your .env file.');
    process.exit(1);
}
/**
 * Fetches stock data from Alpha Vantage API
 * @param symbol Stock symbol (e.g., IBM, AAPL)
 * @param interval Time interval between data points or 'daily' for daily data
 * @param outputsize Amount of data to return (compact or full)
 * @returns Formatted stock data as a string
 */
function getStockData(symbol_1, interval_1) {
    return __awaiter(this, arguments, void 0, function (symbol, interval, outputsize) {
        var symbolStr, intervalStr, outputsizeStr, url, timeSeriesKey, response, timeSeries, formattedData, error_1;
        if (outputsize === void 0) { outputsize = 'compact'; }
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    symbolStr = Array.isArray(symbol) ? symbol[0] : symbol;
                    intervalStr = Array.isArray(interval) ? interval[0] : interval;
                    outputsizeStr = Array.isArray(outputsize) ? outputsize[0] : outputsize;
                    url = void 0;
                    timeSeriesKey = void 0;
                    if (intervalStr === 'daily') {
                        // Use TIME_SERIES_DAILY endpoint
                        url = "".concat(BASE_URL, "?function=TIME_SERIES_DAILY&symbol=").concat(symbolStr, "&outputsize=").concat(outputsizeStr, "&apikey=").concat(API_KEY);
                        timeSeriesKey = 'Time Series (Daily)';
                    }
                    else {
                        // Use TIME_SERIES_INTRADAY endpoint
                        url = "".concat(BASE_URL, "?function=TIME_SERIES_INTRADAY&symbol=").concat(symbolStr, "&interval=").concat(intervalStr, "&outputsize=").concat(outputsizeStr, "&apikey=").concat(API_KEY);
                        timeSeriesKey = "Time Series (".concat(intervalStr, ")");
                    }
                    return [4 /*yield*/, axios_1.default.get(url)];
                case 1:
                    response = _a.sent();
                    // Check for error messages from Alpha Vantage
                    if (response.data['Error Message']) {
                        throw new Error(response.data['Error Message']);
                    }
                    if (response.data['Note']) {
                        console.warn('API Usage Note:', response.data['Note']);
                    }
                    timeSeries = response.data[timeSeriesKey];
                    if (!timeSeries) {
                        throw new Error('No time series data found in the response');
                    }
                    formattedData = formatTimeSeriesData(timeSeries, symbolStr, intervalStr);
                    return [2 /*return*/, formattedData];
                case 2:
                    error_1 = _a.sent();
                    if (axios_1.default.isAxiosError(error_1)) {
                        throw new Error("API request failed: ".concat(error_1.message));
                    }
                    throw error_1;
                case 3: return [2 /*return*/];
            }
        });
    });
}
/**
 * Formats time series data into a readable string
 */
function formatTimeSeriesData(timeSeries, symbol, interval) {
    var dates = Object.keys(timeSeries).sort().reverse(); // Most recent first
    var result = "Stock data for ".concat(symbol.toUpperCase(), " (").concat(interval === 'daily' ? 'Daily' : interval, " intervals):\n\n");
    // Limit to 10 data points to avoid overwhelming responses
    var limitedDates = dates.slice(0, 10);
    for (var _i = 0, limitedDates_1 = limitedDates; _i < limitedDates_1.length; _i++) {
        var date = limitedDates_1[_i];
        var data = timeSeries[date];
        result += "".concat(date, ":\n");
        result += "  Open: ".concat(data['1. open'], "\n");
        result += "  High: ".concat(data['2. high'], "\n");
        result += "  Low: ".concat(data['3. low'], "\n");
        result += "  Close: ".concat(data['4. close'], "\n");
        result += "  Volume: ".concat(data['5. volume'], "\n\n");
    }
    if (dates.length > 10) {
        result += "... and ".concat(dates.length - 10, " more data points available.\n");
    }
    return result;
}
/**
 * Analyzes stock data to generate alerts based on price movements
 * @param symbol Stock symbol (e.g., IBM, AAPL)
 * @param threshold Percentage threshold for price movement alerts
 * @returns Formatted alerts as a string
 */
function getStockAlerts(symbol_1) {
    return __awaiter(this, arguments, void 0, function (symbol, threshold) {
        var symbolStr, url, response, timeSeries, dates, alerts, alertCount, daysToAnalyze, i, currentDate, previousDate, currentClose, previousClose, percentChange, absPercentChange, direction, error_2;
        if (threshold === void 0) { threshold = 5; }
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    symbolStr = Array.isArray(symbol) ? symbol[0] : symbol;
                    url = "".concat(BASE_URL, "?function=TIME_SERIES_DAILY&symbol=").concat(symbolStr, "&outputsize=compact&apikey=").concat(API_KEY);
                    return [4 /*yield*/, axios_1.default.get(url)];
                case 1:
                    response = _a.sent();
                    if (response.data['Error Message']) {
                        throw new Error(response.data['Error Message']);
                    }
                    timeSeries = response.data['Time Series (Daily)'];
                    if (!timeSeries) {
                        throw new Error('No time series data found in the response');
                    }
                    dates = Object.keys(timeSeries).sort().reverse();
                    if (dates.length < 2) {
                        return [2 /*return*/, "Not enough historical data available for ".concat(symbolStr, " to generate alerts.")];
                    }
                    alerts = "Stock Alerts for ".concat(symbolStr.toUpperCase(), " (").concat(threshold, "% threshold):\n\n");
                    alertCount = 0;
                    daysToAnalyze = Math.min(10, dates.length - 1);
                    for (i = 0; i < daysToAnalyze; i++) {
                        currentDate = dates[i];
                        previousDate = dates[i + 1];
                        currentClose = parseFloat(timeSeries[currentDate]['4. close']);
                        previousClose = parseFloat(timeSeries[previousDate]['4. close']);
                        percentChange = ((currentClose - previousClose) / previousClose) * 100;
                        absPercentChange = Math.abs(percentChange);
                        // Check if change exceeds threshold
                        if (absPercentChange >= threshold) {
                            direction = percentChange >= 0 ? 'increased' : 'decreased';
                            alerts += "".concat(currentDate, ": Price ").concat(direction, " by ").concat(absPercentChange.toFixed(2), "% from ").concat(previousClose, " to ").concat(currentClose, "\n");
                            alertCount++;
                        }
                    }
                    if (alertCount === 0) {
                        alerts += "No significant price movements (>=".concat(threshold, "%) detected in the last ").concat(daysToAnalyze, " trading days.\n");
                    }
                    return [2 /*return*/, alerts];
                case 2:
                    error_2 = _a.sent();
                    if (axios_1.default.isAxiosError(error_2)) {
                        throw new Error("API request failed: ".concat(error_2.message));
                    }
                    throw error_2;
                case 3: return [2 /*return*/];
            }
        });
    });
}
