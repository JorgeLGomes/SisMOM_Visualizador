# Multi-stage build: ~12 MB final image
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/tile-cache ./

FROM gcr.io/distroless/static:nonroot
COPY --from=builder /out/tile-cache /tile-cache
EXPOSE 8081
USER nonroot:nonroot
ENTRYPOINT ["/tile-cache"]
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["/tile-cache", "-healthcheck"]
