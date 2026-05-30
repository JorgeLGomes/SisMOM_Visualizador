// gisele tile-cache — proxy + cache do FTP do CPTEC
// Fase 1 do roadmap backend. Endpoint principal:
//   GET /v1/tiles/cptec/{model}/{yyyy}/{mm}/{dd}/{hh}/{kind}/{filename}
// Cache em RAM + disco, headers CORS uniformes, ETag/Last-Modified.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"sync/atomic"
	"time"
)

const (
	serviceName = "tile-cache"
	version     = "0.1.0-skeleton"
)

var (
	requestsTotal atomic.Uint64
	cacheHits     atomic.Uint64
	cacheMisses   atomic.Uint64
	startedAt     = time.Now()
)

type healthResponse struct {
	Service       string  `json:"service"`
	Version       string  `json:"version"`
	UptimeSeconds float64 `json:"uptime_seconds"`
	Requests      uint64  `json:"requests_total"`
	CacheHits     uint64  `json:"cache_hits"`
	CacheMisses   uint64  `json:"cache_misses"`
	CacheHitRate  float64 `json:"cache_hit_rate"`
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/v1/tiles/health", handleHealth)
	mux.HandleFunc("/v1/tiles/", handleTile)

	slog.Info("starting", "service", serviceName, "version", version, "port", port)
	srv := &http.Server{
		Addr:              ":" + port,
		Handler:           withCORS(withLogging(mux)),
		ReadHeaderTimeout: 10 * time.Second,
	}
	if err := srv.ListenAndServe(); err != nil {
		slog.Error("server stopped", "err", err)
		os.Exit(1)
	}
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	hits := cacheHits.Load()
	misses := cacheMisses.Load()
	total := hits + misses
	rate := 0.0
	if total > 0 {
		rate = float64(hits) / float64(total)
	}
	resp := healthResponse{
		Service:       serviceName,
		Version:       version,
		UptimeSeconds: time.Since(startedAt).Seconds(),
		Requests:      requestsTotal.Load(),
		CacheHits:     hits,
		CacheMisses:   misses,
		CacheHitRate:  rate,
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(resp)
}

func handleTile(w http.ResponseWriter, r *http.Request) {
	// SKELETON — Fase 1 implementará:
	//   1) Parse path: /v1/tiles/cptec/{model}/{yyyy}/{mm}/{dd}/{hh}/{kind}/{filename}
	//   2) Compose URL: https://ftp1.cptec.inpe.br/modelos/tempo/{model}/{yyyy}/{mm}/{dd}/{hh}/{kind}/{filename}
	//   3) Check cache (RAM/Redis/MinIO)
	//   4) On miss: fetch FTP, store in cache, serve
	//   5) On hit: serve direct with CORS headers
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotImplemented)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"status":  "not_implemented",
		"message": "tile-cache skeleton — Fase 1 vai implementar o proxy + cache",
		"path":    r.URL.Path,
	})
}

func withCORS(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, Range")
		w.Header().Set("Access-Control-Expose-Headers", "ETag, Last-Modified, Content-Length")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		h.ServeHTTP(w, r)
	})
}

func withLogging(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestsTotal.Add(1)
		t0 := time.Now()
		h.ServeHTTP(w, r)
		slog.Info("request",
			"method", r.Method, "path", r.URL.Path,
			"dur_ms", time.Since(t0).Milliseconds())
	})
}

// drainAndClose é utilitário para o proxy real da Fase 1
func drainAndClose(rc io.ReadCloser) {
	if rc == nil {
		return
	}
	_, _ = io.Copy(io.Discard, rc)
	_ = rc.Close()
}

var _ = fmt.Sprintf // silence unused import in skeleton
