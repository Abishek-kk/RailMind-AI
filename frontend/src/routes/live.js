"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Route = void 0;
var react_router_1 = require("@tanstack/react-router");
var react_1 = require("react");
var react_query_1 = require("@tanstack/react-query");
var TopBar_1 = require("@/components/TopBar");
var StatCard_1 = require("@/components/StatCard");
var CCTVFeedCard_1 = require("@/components/CCTVFeedCard");
var RiskBadge_1 = require("@/components/RiskBadge");
var dialog_1 = require("@/components/ui/dialog");
var lucide_react_1 = require("lucide-react");
var sonner_1 = require("sonner");
var alerts_1 = require("@/lib/api/alerts");
var feeds_1 = require("@/lib/api/feeds");
var useWebSocket_1 = require("@/hooks/useWebSocket");
var mock_data_1 = require("@/lib/mock-data");
function normalizeTrackId(trackId) {
    var parsed = Number(trackId);
    return Number.isFinite(parsed) ? parsed : trackId.split('').reduce(function (sum, char) { return sum + char.charCodeAt(0); }, 0);
}
function mapCameraIdToFeedId(cameraId) {
    var _a;
    var match = cameraId.match(/CCTV(?:[_-]P?(\d+)|[_-]?(\d+))/i);
    var number = match ? Number((_a = match[1]) !== null && _a !== void 0 ? _a : match[2]) : NaN;
    if (Number.isFinite(number) && number > 0) {
        return "CCTV-".concat(number);
    }
    var fallback = cameraId.match(/\d+/);
    return fallback ? "CCTV-".concat(fallback[0]) : cameraId;
}
exports.Route = (0, react_router_1.createFileRoute)("/live")({
    head: function () { return ({ meta: [{ title: "Live Monitoring — RailMind AI" }] }); },
    component: LivePage,
});
function LivePage() {
    var _a, _b;
    var _c = (0, react_1.useState)("all"), feed = _c[0], setFeed = _c[1];
    var _d = (0, react_1.useState)(false), isDialogOpen = _d[0], setIsDialogOpen = _d[1];
    var _e = (0, react_1.useState)(""), cameraId = _e[0], setCameraId = _e[1];
    var _f = (0, react_1.useState)(""), rtspUrl = _f[0], setRtspUrl = _f[1];
    var _g = (0, react_1.useState)(""), platformName = _g[0], setPlatformName = _g[1];
    /** BUG 6 FIX: filter level state for Live Detections sidebar */
    var _h = (0, react_1.useState)("all"), filterLevel = _h[0], setFilterLevel = _h[1];
    /** BUG 15 FIX: allow user to dismiss mock-data banner */
    var _j = (0, react_1.useState)(false), mockBannerDismissed = _j[0], setMockBannerDismissed = _j[1];
    var queryClient = (0, react_query_1.useQueryClient)();
    var _k = (0, react_query_1.useQuery)({ queryKey: ["liveFeeds"], queryFn: feeds_1.getFeeds }), feeds = _k.data, feedsLoading = _k.isLoading, feedsError = _k.error;
    var _l = (0, react_query_1.useQuery)({ queryKey: ["liveAlerts"], queryFn: alerts_1.getAlerts }), alerts = _l.data, alertsLoading = _l.isLoading, alertsError = _l.error;
    var addFeedMutation = (0, react_query_1.useMutation)({
        mutationFn: function (payload) { return (0, feeds_1.createFeed)(payload); },
        onSuccess: function () {
            setIsDialogOpen(false);
            setCameraId("");
            setRtspUrl("");
            setPlatformName("");
            queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
        },
        /** BUG 3 FIX: show error toast on failure; do NOT close dialog */
        onError: function () {
            sonner_1.toast.error("Failed to add feed. Please check the camera ID and URL.");
        },
    });
    var websocketBase = (_a = import.meta.env.VITE_WS_URL) !== null && _a !== void 0 ? _a : "ws://localhost:8000";
    var _m = (0, useWebSocket_1.useWebSocket)("".concat(websocketBase, "/ws/alerts")), latestMessage = _m.data, wsStatus = _m.status, wsError = _m.error;
    var _o = (0, react_1.useState)([]), realtimeAlerts = _o[0], setRealtimeAlerts = _o[1];
    var _p = (0, react_1.useState)({}), feedDetections = _p[0], setFeedDetections = _p[1];
    var _q = (0, react_1.useState)(true), soundEnabled = _q[0], setSoundEnabled = _q[1];
    var shownToastIds = (0, react_1.useRef)(new Set());
    (0, react_1.useEffect)(function () {
        if (wsError) {
            sonner_1.toast.error("Real-time updates unavailable: ".concat(wsError));
        }
    }, [wsError]);
    var playNotificationSound = (0, react_1.useCallback)(function () {
        if (typeof window === "undefined") {
            return;
        }
        try {
            var AudioCtx = window.AudioContext || window.webkitAudioContext;
            var context_1 = new AudioCtx();
            var oscillator = context_1.createOscillator();
            var gain = context_1.createGain();
            oscillator.type = "sine";
            oscillator.frequency.value = 880;
            gain.gain.setValueAtTime(0.12, context_1.currentTime);
            oscillator.connect(gain);
            gain.connect(context_1.destination);
            oscillator.start();
            oscillator.stop(context_1.currentTime + 0.14);
            oscillator.onended = function () {
                context_1.close().catch(function () { return undefined; });
            };
        }
        catch (_a) {
            // Ignore audio failures in unsupported browsers or restricted contexts.
        }
    }, []);
    var showAlertToast = (0, react_1.useCallback)(function (alert) {
        if (shownToastIds.current.has(alert.backendId)) {
            return;
        }
        shownToastIds.current.add(alert.backendId);
        var message = "".concat(alert.cctv, " \u2014 ").concat(alert.type, " \u2014 Risk: ").concat(alert.riskScore, "%");
        var isHighRisk = alert.riskLevel === "high";
        var isMediumRisk = alert.riskLevel === "medium" || alert.riskLevel === "suspicious";
        var icon = (<span className={"inline-flex h-3.5 w-3.5 rounded-full ".concat(isHighRisk ? "bg-red-500" : isMediumRisk ? "bg-orange-500" : "bg-emerald-500")}/>);
        var options = {
            icon: icon,
            duration: isHighRisk ? Infinity : 5000,
        };
        if (isHighRisk) {
            sonner_1.toast.error(message, options);
        }
        else if (alert.riskLevel === "low") {
            sonner_1.toast.success(message, options);
        }
        else {
            (0, sonner_1.toast)(message, options);
        }
        if (isHighRisk && soundEnabled) {
            playNotificationSound();
        }
    }, [playNotificationSound, soundEnabled]);
    var isMockData = (0, react_1.useMemo)(function () {
        return Array.isArray(feeds) && feeds.length === 0 && import.meta.env.MODE === "development";
    }, [feeds]);
    var displayFeeds = (0, react_1.useMemo)(function () {
        if (!Array.isArray(feeds)) {
            return (0, mock_data_1.getLiveFeeds)();
        }
        if (feeds.length === 0 && import.meta.env.MODE === "development") {
            return (0, mock_data_1.getLiveFeeds)();
        }
        return feeds;
    }, [feeds]);
    var filteredFeeds = (0, react_1.useMemo)(function () {
        var list = displayFeeds;
        return feed === "all" ? list : list.filter(function (f) { return f.id === feed; });
    }, [displayFeeds, feed]);
    (0, react_1.useEffect)(function () {
        if (alerts) {
            setRealtimeAlerts(alerts);
        }
    }, [alerts]);
    (0, react_1.useEffect)(function () {
        if (!latestMessage) {
            return;
        }
        /**
         * BUG 2 FIX: detect backend alert payloads by checking for fields that
         * only exist on raw BackendAlert objects — NOT by checking for "backendId"
         * which is only added after mapping.
         */
        if ("risk_score" in latestMessage && "incident_type" in latestMessage) {
            var mappedAlert_1 = (0, alerts_1.mapBackendAlert)(latestMessage);
            setRealtimeAlerts(function (current) {
                if (current.some(function (a) { return a.backendId === mappedAlert_1.backendId; })) {
                    return current;
                }
                return __spreadArray([mappedAlert_1], current, true);
            });
            showAlertToast(mappedAlert_1);
            return;
        }
        if ("camera_id" in latestMessage && Array.isArray(latestMessage.detections)) {
            var latestDetection = latestMessage;
            var feedId_1 = mapCameraIdToFeedId(latestDetection.camera_id);
            var _a = latestDetection.dimensions || {}, width = _a.width, height = _a.height;
            var safeWidth_1 = width || 1;
            var safeHeight_1 = height || 1;
            var boxes_1 = latestDetection.detections.map(function (detection) {
                var _a = detection.bbox, x1 = _a[0], y1 = _a[1], x2 = _a[2], y2 = _a[3];
                var normalizedLevel = (detection.risk_level.toLowerCase().includes("high")
                    ? "high"
                    : detection.risk_level.toLowerCase().includes("suspicious")
                        ? "suspicious"
                        : detection.risk_level.toLowerCase().includes("medium")
                            ? "medium"
                            : "low");
                return {
                    id: normalizeTrackId(detection.track_id),
                    level: normalizedLevel,
                    x: Math.max(0, Math.min(100, (x1 / safeWidth_1) * 100)),
                    y: Math.max(0, Math.min(100, (y1 / safeHeight_1) * 100)),
                    w: Math.max(0, Math.min(100, ((x2 - x1) / safeWidth_1) * 100)),
                    h: Math.max(0, Math.min(100, ((y2 - y1) / safeHeight_1) * 100)),
                };
            });
            setFeedDetections(function (current) {
                var _a;
                return (__assign(__assign({}, current), (_a = {}, _a[feedId_1] = boxes_1, _a)));
            });
            return;
        }
    }, [latestMessage, showAlertToast]);
    var filteredAlerts = (0, react_1.useMemo)(function () {
        var list = realtimeAlerts;
        if (feed !== "all") {
            list = list.filter(function (a) { return a.cctv === feed; });
        }
        if (filterLevel !== "all") {
            list = list.filter(function (a) {
                if (filterLevel === "medium") {
                    return a.riskLevel === "medium" || a.riskLevel === "suspicious";
                }
                return a.riskLevel === filterLevel;
            });
        }
        return list;
    }, [realtimeAlerts, feed, filterLevel]);
    var totalPeople = filteredFeeds.reduce(function (s, f) { return s + f.peopleDetected; }, 0);
    var active = filteredAlerts.filter(function (a) { return a.status === "active"; }).length;
    var highRisk = filteredAlerts.filter(function (a) { return a.riskLevel === "high"; }).length;
    /** Build dynamic feeds list for TopBar (BUG 12) */
    var dynamicFeeds = (0, react_1.useMemo)(function () {
        if (!Array.isArray(feeds) || feeds.length === 0)
            return undefined;
        return feeds.map(function (f) { return ({ id: f.id, label: "".concat(f.id, " (").concat(f.platform, ")") }); });
    }, [feeds]);
    return (<div>
      <TopBar_1.TopBar title="Live Monitoring" subtitle="Real-time CCTV Monitoring & Threat Detection" selectedFeed={feed} onFeedChange={setFeed} soundEnabled={soundEnabled} onSoundToggle={function () { return setSoundEnabled(function (enabled) { return !enabled; }); }} feeds={dynamicFeeds}/>
      <div className="p-6">
        {wsError ? (<div className="mb-6 rounded-xl border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
            Real-time updates are blocked. {wsError}
          </div>) : null}
        {feedsLoading || alertsLoading ? (<div className="space-y-4">
            <div className="h-6 w-1/3 rounded bg-muted/30 animate-pulse"/>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
              {Array.from({ length: 5 }).map(function (_, index) { return (<div key={index} className="h-24 rounded-xl bg-muted/20 p-4 animate-pulse"/>); })}
            </div>
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
              <div className="space-y-4">
                {Array.from({ length: 2 }).map(function (_, index) { return (<div key={index} className="h-80 rounded-xl bg-muted/20 p-4 animate-pulse"/>); })}
              </div>
              <div className="h-[640px] rounded-xl bg-muted/20 p-4 animate-pulse"/>
            </div>
          </div>) : feedsError || alertsError ? (<div className="rounded-xl border border-border bg-card p-6 text-center text-sm text-destructive">
            Unable to load live monitoring data. Please refresh the page.
          </div>) : (<>
            {/* BUG 15 FIX: visible yellow banner when showing mock feeds in development */}
            {isMockData && !mockBannerDismissed && (<div className="mb-4 flex items-center justify-between rounded-xl border border-yellow-500/40 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-400">
                <span>⚠ Showing mock feeds — no camera feeds registered in backend.</span>
                <button type="button" onClick={function () { return setMockBannerDismissed(true); }} className="ml-4 rounded px-2 py-0.5 text-xs font-medium text-yellow-300 hover:bg-yellow-500/20">
                  Dismiss
                </button>
              </div>)}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <StatCard_1.StatCard label="Total CCTV Feeds" value={(_b = feeds === null || feeds === void 0 ? void 0 : feeds.length) !== null && _b !== void 0 ? _b : 0} sublabel="Active Cameras" icon={lucide_react_1.Camera} iconColor="#3b82f6" iconBg="rgba(59,130,246,0.15)"/>
          <StatCard_1.StatCard label="People Detected" value={totalPeople} sublabel="Across All Feeds" icon={lucide_react_1.Users} iconColor="#22c55e" iconBg="rgba(34,197,94,0.15)"/>
          <StatCard_1.StatCard label="Active Alerts" value={active} sublabel="Across All Feeds" icon={lucide_react_1.AlertTriangle} iconColor="#f97316" iconBg="rgba(249,115,22,0.15)"/>
          <StatCard_1.StatCard label="High Risk Detected" value={highRisk} sublabel="Require Attention" icon={lucide_react_1.Activity} iconColor="#ef4444" iconBg="rgba(239,68,68,0.15)"/>
          <button type="button" onClick={function () { return setIsDialogOpen(true); }} className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/30 transition-transform hover:scale-[1.02]">
            <lucide_react_1.Plus className="h-4 w-4"/> Add CCTV Feed
          </button>
          <dialog_1.Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <dialog_1.DialogContent>
              <dialog_1.DialogHeader>
                <dialog_1.DialogTitle>Add CCTV Feed</dialog_1.DialogTitle>
                <dialog_1.DialogDescription>
                  Add a new camera stream so the live dashboard can monitor it in real time.
                </dialog_1.DialogDescription>
              </dialog_1.DialogHeader>
              <form onSubmit={function (event) {
                event.preventDefault();
                /** BUG 1 FIX: pass source_url instead of url */
                addFeedMutation.mutate({
                    id: cameraId,
                    name: platformName,
                    source_url: rtspUrl,
                });
            }} className="space-y-4">
                <div className="space-y-1 text-sm">
                  <label className="block font-medium">Camera ID</label>
                  <input value={cameraId} onChange={function (event) { return setCameraId(event.target.value); }} placeholder="CCTV_P3_01" className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20" required/>
                </div>
                <div className="space-y-1 text-sm">
                  <label className="block font-medium">RTSP Stream URL</label>
                  <input value={rtspUrl} onChange={function (event) { return setRtspUrl(event.target.value); }} placeholder="rtsp://username:password@camera.local/stream" className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20" required/>
                </div>
                <div className="space-y-1 text-sm">
                  <label className="block font-medium">Platform Name</label>
                  <input value={platformName} onChange={function (event) { return setPlatformName(event.target.value); }} placeholder="Platform 3 South" className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20" required/>
                </div>
                <dialog_1.DialogFooter>
                  <button type="button" onClick={function () { return setIsDialogOpen(false); }} className="inline-flex items-center justify-center rounded-xl border border-border bg-secondary px-4 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-secondary/80">
                    Cancel
                  </button>
                  <button type="submit" disabled={addFeedMutation.isPending} className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition disabled:cursor-not-allowed disabled:opacity-60">
                    {addFeedMutation.isPending ? "Adding..." : "Add Feed"}
                  </button>
                </dialog_1.DialogFooter>
              </form>
            </dialog_1.DialogContent>
          </dialog_1.Dialog>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
          {filteredFeeds.length === 0 ? (<div className="rounded-xl border border-border bg-card p-8 text-center">
              <h2 className="text-xl font-semibold text-foreground">No camera feeds registered yet</h2>
              <p className="mt-3 text-sm text-muted-foreground">
                No camera feeds registered yet. Click "Add CCTV Feed" to get started.
              </p>
            </div>) : (<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {filteredFeeds.map(function (f) { return (<CCTVFeedCard_1.CCTVFeedCard key={f.id} feed={f} detections={feedDetections[f.id]}/>); })}
            </div>)}

          <aside className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h3 className="text-sm font-semibold">Live Detections</h3>
              {/* BUG 6 FIX: working filter dropdown */}
              <select id="live-detections-filter" value={filterLevel} onChange={function (e) { return setFilterLevel(e.target.value); }} className="rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50">
                <option value="all">All Alerts</option>
                <option value="high">High Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="low">Low Risk</option>
              </select>
            </div>
            <div className="max-h-[640px] space-y-3 overflow-y-auto p-3">
              {filteredAlerts.slice(0, 6).map(function (a) {
                var c = (0, mock_data_1.riskColor)(a.riskLevel);
                return (<div key={a.id} className="flex gap-3 rounded-lg border p-3 transition-colors hover:bg-secondary/40" style={{ borderColor: "".concat(c, "33"), backgroundColor: "".concat(c, "0a") }}>
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] text-muted-foreground">{a.time}</div>
                      <div className="text-[11px] text-muted-foreground">{a.cctv} / {a.platform}</div>
                      <div className="mt-1 truncate text-sm font-semibold">{a.type}</div>
                      <div className="mt-1 text-xs">
                        Risk Score: <span className="font-bold" style={{ color: c }}>{a.riskScore}%</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <img src={a.image} alt="" className="h-14 w-20 rounded object-cover" loading="lazy"/>
                      <RiskBadge_1.RiskBadge level={a.riskLevel}/>
                    </div>
                  </div>);
            })}
            </div>
            <div className="border-t border-border p-3 text-center">
              <react_router_1.Link to="/alerts" className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
                View All Alerts <lucide_react_1.ArrowRight className="h-4 w-4"/>
              </react_router_1.Link>
            </div>
          </aside>
        </div>
          </>)}
      </div>
    </div>);
}
