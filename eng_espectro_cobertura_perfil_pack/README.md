# Pacote — Cobertura (AOI) e Perfil TX↔RX (Curvatura da Terra)

## Conteúdo
- `coverage_profile_spec.md` — especificação completa (cobertura + perfil).
- `frontend/types/linkProfile.ts` — tipos.
- `frontend/lib/linkProfileMath.ts` — matemática de curvatura/Fresnel/obstrução.
- `frontend/components/LinkProfileChartCanvas.tsx` — gráfico Canvas (curvatura escura na base + terreno + LOS + Fresnel).
- `frontend/components/LinkProfilePanel.tsx` — header + gráfico.
- `frontend/api/linkProfile.ts` — cliente para `POST /api/links/profile`.

## Integração (React + Vite)
1) Copie a pasta `frontend/` para o seu projeto Vite (ajuste paths conforme seu alias).
2) Crie um painel dockado (ou modal) que renderize:
   - `<LinkProfilePanel data={profileData} onClose={...} />`

## Fluxo (Mapa → Perfil)
- O mapa (Leaflet) deve operar em modo "Link/Perfil":
  - clique 1 define TX
  - clique 2 define RX
  - então chame o backend: `fetchLinkProfile(...)`
  - renderize o painel com a resposta

## Backend esperado
Endpoint:
- `POST /api/links/profile`

Deve retornar:
- `samples`: array com `{d_m, ground_m}`
- `derived`: distância, azimute, ângulo de elevação, obstrução/worst fresnel
- (opcional) `model_results` com path loss / campo / rx level

> Importante: o gráfico desenha exatamente:
> - Fill escuro: `y_base → y_earth = y_base + bulge`
> - Fill claro: `y_earth → y_terrain = y_earth + ground`
> Onde `bulge(x)=x(D-x)/(2*k*R_earth)`

