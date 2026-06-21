import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from pydantic import TypeAdapter

from config.settings import AzureConfig, load_embeddings, load_llm
from evaluation.judge import run_batch_evaluation
from orchestrator.graph import build_graph, run_retention_review
from schemas.customer import CustomerRecord
from schemas.playbook import RetentionPlaybook
from schemas.response import AgentResponseRecord
from schemas.risk import RiskSegment
from tools.agent_tools import initialize_tools


def _load_data(data_dir: Path) -> tuple[
    dict[str, CustomerRecord], list[RiskSegment], list[RetentionPlaybook]
]:
    """Load and validate JSON configuration data from the specified directory."""
    print(f"Loading data from {data_dir}...")

    # Load customers
    customers_path = data_dir / "customer_records.json"
    if not customers_path.exists():
        raise FileNotFoundError(f"Customer records not found at {customers_path}")
    with open(customers_path, "r", encoding="utf-8") as f:
        customers_list = TypeAdapter(list[CustomerRecord]).validate_python(json.load(f))
    customer_pool = {c.customer_id: c for c in customers_list}
    print(f"Loaded {len(customer_pool)} customers.")

    # Load risk segments (optional: could be hardcoded, but keeping data-driven)
    segments_path = data_dir / "risk_segments.json"
    if not segments_path.exists():
        raise FileNotFoundError(f"Risk segments not found at {segments_path}")
    with open(segments_path, "r", encoding="utf-8") as f:
        risk_segments = TypeAdapter(list[RiskSegment]).validate_python(json.load(f))
    print(f"Loaded {len(risk_segments)} risk segments.")

    # Load playbooks
    playbooks_path = data_dir / "retention_playbooks.json"
    if not playbooks_path.exists():
        raise FileNotFoundError(f"Retention playbooks not found at {playbooks_path}")
    with open(playbooks_path, "r", encoding="utf-8") as f:
        playbooks = TypeAdapter(list[RetentionPlaybook]).validate_python(json.load(f))
    print(f"Loaded {len(playbooks)} retention playbooks.")

    return customer_pool, risk_segments, playbooks


def _setup_retriever(playbooks: list[RetentionPlaybook], embeddings):
    """Build the ChromaDB vector store and return a retriever."""
    print("Building ChromaDB vector store...")
    playbook_docs = [
        Document(
            page_content=playbook.to_rag_text(),
            metadata={"segment": playbook.segment, "playbook_id": playbook.id},
        )
        for playbook in playbooks
    ]

    vectorstore = Chroma.from_documents(
        documents=playbook_docs,
        embedding=embeddings,
        collection_name="retention_playbooks",
        persist_directory="./chroma_db",
    )

    return vectorstore.as_retriever(search_kwargs={"k": 1})


def command_review(args):
    """Handle the 'review' command (single or batch)."""
    # 1. Setup config & LLMs
    try:
        config = AzureConfig.from_env()
        config.validate_complete()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure your .env file is properly configured.")
        sys.exit(1)

    llm = load_llm(config)
    embeddings = load_embeddings(config)

    # 2. Load data
    data_dir = Path(args.data_dir)
    try:
        customer_pool, _, playbooks = _load_data(data_dir)
    except Exception as e:
        print(f"Data Loading Error: {e}")
        sys.exit(1)

    # 3. Setup RAG and Tools
    retriever = _setup_retriever(playbooks, embeddings)
    initialize_tools(customer_pool, retriever)

    # 4. Build Graph
    graph = build_graph(llm, playbooks)

    # 5. Execute Review
    if args.customer_id:
        # Single customer mode
        cid = args.customer_id
        if cid not in customer_pool:
            print(f"Error: Customer ID '{cid}' not found in {data_dir}/customer_records.json")
            sys.exit(1)

        print(f"\n{'=' * 60}")
        print(f"REVIEWING CUSTOMER: {cid}")
        print(f"{'=' * 60}")
        response = run_retention_review(graph, cid)
        print(response)

    elif args.all:
        # Batch mode
        print("\nStarting batch review...")
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        results: list[AgentResponseRecord] = []
        for cid in customer_pool.keys():
            print(f"Processing {cid}...", end=" ", flush=True)
            try:
                response = run_retention_review(graph, cid)
                results.append(AgentResponseRecord(customer_id=cid, agent_response=response))
                print("OK")
            except Exception as e:
                print(f"ERROR: {e}")
                results.append(AgentResponseRecord(customer_id=cid, agent_response=f"ERROR: {e}"))

        df = pd.DataFrame([r.model_dump() for r in results])
        df.to_csv(output_file, index=False)
        print(f"\nBatch review complete. Results saved to {output_file}")


def command_evaluate(args):
    """Handle the 'evaluate' command using LLM-as-Judge."""
    # 1. Setup config & LLMs
    try:
        config = AzureConfig.from_env()
        config.validate_complete()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    llm = load_llm(config)
    embeddings = load_embeddings(config)

    # 2. Load generated results and reference data
    data_dir = Path(args.data_dir)
    results_path = Path(args.results_file)
    ref_path = data_dir / "validation_results.csv"

    if not results_path.exists():
        print(f"Error: Generated results file not found at {results_path}")
        print("Run 'python main.py review --all' first.")
        sys.exit(1)

    if not ref_path.exists():
        print(f"Error: Reference validation file not found at {ref_path}")
        sys.exit(1)

    print("Loading data for evaluation...")
    results_df = pd.read_csv(results_path)
    ref_df = pd.read_csv(ref_path)

    # Merge to align generated vs reference
    eval_df = results_df.merge(ref_df, on="customer_id", how="inner")
    if eval_df.empty:
        print("Error: No overlapping customer IDs between results and reference files.")
        sys.exit(1)

    print(f"Evaluating {len(eval_df)} records using LLM-as-Judge...")
    
    # 3. Run Evaluation
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    eval_results_df = run_batch_evaluation(eval_df, llm, embeddings)
    eval_results_df.to_csv(output_file, index=False)
    print(f"\nEvaluation complete. Detailed judgments saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Customer Retention Intelligence - Multi-Agent CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: review
    parser_review = subparsers.add_parser("review", help="Run retention review for customers")
    group = parser_review.add_mutually_exclusive_group(required=True)
    group.add_argument("--customer-id", type=str, help="Single customer ID to review")
    group.add_argument("--all", action="store_true", help="Review all customers in the dataset")
    parser_review.add_argument(
        "--data-dir", type=str, default="./data/sample", help="Directory containing input JSON files"
    )
    parser_review.add_argument(
        "--output", type=str, default="./output/results.csv", help="Output file path (for --all)"
    )

    # Subcommand: evaluate
    parser_eval = subparsers.add_parser("evaluate", help="Evaluate generated results vs references")
    parser_eval.add_argument(
        "--results-file", type=str, default="./output/results.csv", help="CSV file containing agent responses"
    )
    parser_eval.add_argument(
        "--data-dir", type=str, default="./data/sample", help="Directory containing validation_results.csv reference"
    )
    parser_eval.add_argument(
        "--output", type=str, default="./output/quality_judgments.csv", help="Output judgments CSV file"
    )

    args = parser.parse_args()

    # Create default output dir if it doesn't exist
    Path("./output").mkdir(exist_ok=True)

    if args.command == "review":
        command_review(args)
    elif args.command == "evaluate":
        command_evaluate(args)


if __name__ == "__main__":
    main()
