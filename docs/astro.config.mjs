import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import starlightThemeGalaxy from "starlight-theme-galaxy";

export default defineConfig({
  site: "https://rennerdo30.github.io/excel-translate",
  base: "/excel-translate",
  integrations: [
    starlight({
      title: "Excel Translate",
      description:
        "Excel for Mac custom functions that translate cells through a local LM Studio model.",
      plugins: [starlightThemeGalaxy()],
      customCss: ["./src/styles/custom.css"],
      social: [
        { icon: "github", label: "GitHub", href: "https://github.com/rennerdo30/excel-translate" },
      ],
      sidebar: [
        {
          label: "Getting Started",
          items: [
            { label: "Introduction", slug: "index" },
            { label: "Installation", slug: "getting-started/installation" },
            { label: "Configuration", slug: "getting-started/configuration" },
          ],
        },
        {
          label: "Guides",
          items: [
            { label: "Formula Reference", slug: "guides/formulas" },
            { label: "Architecture", slug: "guides/architecture" },
            { label: "Troubleshooting", slug: "guides/troubleshooting" },
          ],
        },
      ],
    }),
  ],
});
