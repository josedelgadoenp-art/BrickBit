"""CLI de conectores — pensado para cron, no solo para el botón de la UI.

    python -m brickbit.connectors --listar
    python -m brickbit.connectors permisos_cdmx
    python -m brickbit.connectors permisos_cdmx --fixture --limite 200
    python -m brickbit.connectors --buscar "manifestacion construccion"

Cron diario a las 7:00 (antes de que abra la fuerza de ventas):

    0 7 * * *  cd /ruta/BrickBit && python -m brickbit.connectors permisos_cdmx >> logs/ingesta.log 2>&1

Sale con código 1 si la ingesta falló, para que el cron lo reporte.
"""

import argparse
import sys
from datetime import datetime

from . import CONECTORES
from .base import ErrorFuente


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m brickbit.connectors",
        description="Ejecuta conectores de ingesta de señales de intención.",
    )
    parser.add_argument("conector", nargs="?", help="clave del conector a ejecutar")
    parser.add_argument("--listar", action="store_true", help="lista los conectores disponibles")
    parser.add_argument("--fixture", action="store_true",
                        help="fuerza el uso de la muestra local en vez de la API")
    parser.add_argument("--limite", type=int, default=1000,
                        help="máximo de registros a leer (default: 1000)")
    parser.add_argument("--buscar", metavar="CONSULTA",
                        help="busca datasets en el catálogo CKAN y muestra sus resource_id")
    args = parser.parse_args(argv)

    if args.listar or (not args.conector and not args.buscar):
        print("Conectores disponibles:\n")
        for clave, info in CONECTORES.items():
            print(f"  {clave:<18} {info['label']}")
            print(f"  {'':<18} señal: {info['senal']}\n")
        return 0

    if args.buscar:
        from . import permisos_cdmx
        try:
            recursos = permisos_cdmx.buscar_recursos(args.buscar)
        except ErrorFuente as e:
            print(f"❌ No se pudo consultar el catálogo: {e}", file=sys.stderr)
            return 1
        if not recursos:
            print("Sin resultados con datastore activo para esa consulta.")
            return 0
        print(f"{len(recursos)} recurso(s) consultables vía API:\n")
        for r in recursos:
            print(f"  {r['dataset']}\n    recurso : {r['recurso']} [{r['formato']}]"
                  f"\n    export BRICKBIT_PERMISOS_RESOURCE_ID={r['resource_id']}\n")
        return 0

    if args.conector not in CONECTORES:
        print(f"❌ Conector desconocido: {args.conector}", file=sys.stderr)
        print(f"   Disponibles: {', '.join(CONECTORES)}", file=sys.stderr)
        return 1

    from .. import db

    conn = db.get_conn()
    inicio = datetime.now()
    resultado = CONECTORES[args.conector]["modulo"].ingestar(
        conn, limite=args.limite, forzar_fixture=args.fixture
    )
    duracion = (datetime.now() - inicio).total_seconds()

    print(f"[{inicio:%Y-%m-%d %H:%M:%S}] {resultado.resumen()} ({duracion:.1f}s)")
    for aviso in resultado.avisos:
        print(f"  ⚠️  {aviso}")
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    sys.exit(main())
