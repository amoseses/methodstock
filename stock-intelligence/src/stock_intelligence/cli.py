import argparse, json
from .pipeline import run_scan, run_backtest

def main():
    parser=argparse.ArgumentParser(description="Stock Intelligence")
    sub=parser.add_subparsers(dest="command",required=True)
    scan=sub.add_parser("scan",help="Analyze current stocks and current news")
    scan.add_argument("--seed",type=int,default=None)
    scan.add_argument("--tickers",nargs="*",default=None)
    bt=sub.add_parser("backtest",help="Technical-only historical backtest")
    bt.add_argument("--period",default="2y")
    bt.add_argument("--tickers",nargs="*",default=None)
    args=parser.parse_args()
    if args.command=="scan":
        result=run_scan(args.tickers,args.seed)
        print(json.dumps({"scanned_at":result["scanned_at"],"selected":result["selected_tickers"],
                          "successful":len(result["results"]),"errors":result["errors"]},indent=2))
        for r in result["results"]:
            print(f'{r["ticker"]:6} price={r["price"]:.2f} tech={r["technical_score"]:>6.1f} '
                  f'news={r["news_score"]:>6.1f} combined={r["combined_score"]:>6.1f} '
                  f'signal={r["signals"]["combined"]["decision"]} news_status={r["news_status"]}')
    else:
        print(run_backtest(args.tickers,args.period).to_string(index=False))

if __name__=="__main__": main()
