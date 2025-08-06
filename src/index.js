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
var mcp_js_1 = require("@modelcontextprotocol/sdk/server/mcp.js");
var stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
var zod_1 = require("zod");
var dotenv_1 = require("dotenv");
var alphaVantage_js_1 = require("./alphaVantage.js");
// Load environment variables
dotenv_1.default.config();
// Create an MCP server
var server = new mcp_js_1.McpServer({
    name: "alpha-vantage-stock-data",
    version: "1.0.0"
});
// Add a resource for stock data
server.resource("stock-data", new mcp_js_1.ResourceTemplate("stock://{symbol}/{interval}", { list: undefined }), function (uri_1, _a) { return __awaiter(void 0, [uri_1, _a], void 0, function (uri, _b) {
    var intervalStr, data, error_1;
    var symbol = _b.symbol, _c = _b.interval, interval = _c === void 0 ? "daily" : _c;
    return __generator(this, function (_d) {
        switch (_d.label) {
            case 0:
                _d.trys.push([0, 2, , 3]);
                intervalStr = Array.isArray(interval) ? interval[0] : interval;
                return [4 /*yield*/, (0, alphaVantage_js_1.getStockData)(symbol, intervalStr === "daily" ? "daily" : intervalStr, "compact")];
            case 1:
                data = _d.sent();
                return [2 /*return*/, {
                        contents: [{
                                uri: uri.href,
                                text: data,
                                mimeType: "text/plain"
                            }]
                    }];
            case 2:
                error_1 = _d.sent();
                throw new Error("Failed to fetch stock data: ".concat(error_1 instanceof Error ? error_1.message : String(error_1)));
            case 3: return [2 /*return*/];
        }
    });
}); });
// Add a tool to get stock data
server.tool("get-stock-data", {
    symbol: zod_1.z.string().describe("Stock symbol (e.g., IBM, AAPL)"),
    interval: zod_1.z.enum(["1min", "5min", "15min", "30min", "60min"]).optional().describe("Time interval between data points (default: 5min)"),
    outputsize: zod_1.z.enum(["compact", "full"]).optional().describe("Amount of data to return (compact: latest 100 data points, full: up to 20 years of data)")
}, function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
    var data, error_2;
    var symbol = _b.symbol, _c = _b.interval, interval = _c === void 0 ? "5min" : _c, _d = _b.outputsize, outputsize = _d === void 0 ? "compact" : _d;
    return __generator(this, function (_e) {
        switch (_e.label) {
            case 0:
                _e.trys.push([0, 2, , 3]);
                return [4 /*yield*/, (0, alphaVantage_js_1.getStockData)(symbol, interval, outputsize)];
            case 1:
                data = _e.sent();
                return [2 /*return*/, {
                        content: [{ type: "text", text: data }]
                    }];
            case 2:
                error_2 = _e.sent();
                return [2 /*return*/, {
                        content: [{ type: "text", text: "Error fetching stock data: ".concat(error_2 instanceof Error ? error_2.message : String(error_2)) }],
                        isError: true
                    }];
            case 3: return [2 /*return*/];
        }
    });
}); });
// Add a tool to get stock alerts based on price movements
server.tool("get-stock-alerts", {
    symbol: zod_1.z.string().describe("Stock symbol (e.g., IBM, AAPL)"),
    threshold: zod_1.z.number().optional().describe("Percentage threshold for price movement alerts (default: 5)")
}, function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
    var alerts, error_3;
    var symbol = _b.symbol, _c = _b.threshold, threshold = _c === void 0 ? 5 : _c;
    return __generator(this, function (_d) {
        switch (_d.label) {
            case 0:
                _d.trys.push([0, 2, , 3]);
                return [4 /*yield*/, (0, alphaVantage_js_1.getStockAlerts)(symbol, threshold)];
            case 1:
                alerts = _d.sent();
                return [2 /*return*/, {
                        content: [{ type: "text", text: alerts }]
                    }];
            case 2:
                error_3 = _d.sent();
                return [2 /*return*/, {
                        content: [{ type: "text", text: "Error generating stock alerts: ".concat(error_3 instanceof Error ? error_3.message : String(error_3)) }],
                        isError: true
                    }];
            case 3: return [2 /*return*/];
        }
    });
}); });
// Add a tool to get daily stock data
server.tool("get-daily-stock-data", {
    symbol: zod_1.z.string().describe("Stock symbol (e.g., IBM, AAPL)"),
    outputsize: zod_1.z.enum(["compact", "full"]).optional().describe("Amount of data to return (compact: latest 100 data points, full: up to 20 years of data)")
}, function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
    var data, error_4;
    var symbol = _b.symbol, _c = _b.outputsize, outputsize = _c === void 0 ? "compact" : _c;
    return __generator(this, function (_d) {
        switch (_d.label) {
            case 0:
                _d.trys.push([0, 2, , 3]);
                return [4 /*yield*/, (0, alphaVantage_js_1.getStockData)(symbol, "daily", outputsize)];
            case 1:
                data = _d.sent();
                return [2 /*return*/, {
                        content: [{ type: "text", text: data }]
                    }];
            case 2:
                error_4 = _d.sent();
                return [2 /*return*/, {
                        content: [{ type: "text", text: "Error fetching daily stock data: ".concat(error_4 instanceof Error ? error_4.message : String(error_4)) }],
                        isError: true
                    }];
            case 3: return [2 /*return*/];
        }
    });
}); });
function main() {
    return __awaiter(this, void 0, void 0, function () {
        var transport, error_5;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    transport = new stdio_js_1.StdioServerTransport();
                    // Connect the server to the transport
                    return [4 /*yield*/, server.connect(transport)];
                case 1:
                    // Connect the server to the transport
                    _a.sent();
                    console.error("Alpha Vantage Stock MCP Server running on stdio");
                    return [3 /*break*/, 3];
                case 2:
                    error_5 = _a.sent();
                    console.error("Error starting server:", error_5);
                    process.exit(1);
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
main();
