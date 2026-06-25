module.exports = {
  apps: [
    {
      name: "odyssey-backend",
      script: "./venv/bin/uvicorn",
      args: "server:app --host 0.0.0.0 --port 8000",
      cwd: "./backend",
      interpreter: "none",
      env: {
        NODE_ENV: "production",
      }
    },
    {
      name: "odyssey-frontend",
      script: "npm",
      args: "run start",
      cwd: "./frontend",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
      }
    }
  ]
};
