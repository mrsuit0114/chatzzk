import { Hono } from "hono";
const app = new Hono<{ Bindings: Env }>();

// 프론트엔드와 충돌하지 않기위해 /api prefix를 사용할 것
app.get("/api/", (c) => c.json({ name: "Cloudaaaaaflare" }));

export default app;
