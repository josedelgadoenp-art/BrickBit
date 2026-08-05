"""BrickBit — Motor de prospección predictiva.

Dos verticales:
  - Seguros GNP (vida, GMM, autos, hogar, empresarial)
  - Mercado inmobiliario (compradores, inversionistas, desarrolladores)

Módulos:
  config     — ICPs, catálogo de señales de intención, pesos
  db         — persistencia SQLite (leads, señales, capturas, reuniones)
  demo_data  — dataset sintético determinista para la demo
  scoring    — motor Fit x Intención -> prioridad A/B/C
  outreach   — generador de Muestreo Inverso (plantillas + Claude opcional)
"""

__version__ = "0.1.0"
