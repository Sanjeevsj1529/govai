/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      colors: {
        night: "#070b17",
        neon: {
          blue: "#36d1ff",
          cyan: "#68f7ff",
          purple: "#8a5dff",
          pink: "#d45dff",
          green: "#46ff9b",
          amber: "#ffce66",
          red: "#ff5c85"
        }
      },
      boxShadow: {
        neon: "0 0 25px rgba(54, 209, 255, 0.18), 0 0 55px rgba(138, 93, 255, 0.14)",
        glow: "0 0 0 1px rgba(255,255,255,0.08), 0 20px 50px rgba(8, 15, 40, 0.35)"
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)"
      },
      keyframes: {
        floaty: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" }
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 18px rgba(54, 209, 255, 0.2)" },
          "50%": { boxShadow: "0 0 30px rgba(138, 93, 255, 0.28)" }
        },
        scan: {
          "0%": { transform: "translateX(-140%)" },
          "100%": { transform: "translateX(160%)" }
        }
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
        pulseGlow: "pulseGlow 3.2s ease-in-out infinite",
        scan: "scan 4.8s linear infinite"
      }
    }
  },
  plugins: []
};
