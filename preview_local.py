from __future__ import annotations

from pathlib import Path

import yaml

from src.journal_metrics import enrich_metrics_many
from src.render import write_outputs
from src.summary import enrich_items


BASE_DIR = Path(__file__).resolve().parent


def sample_items() -> list[dict]:
    return [
        {
            "source": "PubMed",
            "topic": "stem_cell_exosome",
            "topic_cn": "干细胞与外泌体",
            "id": "sample:tbi-ev",
            "pmid": "00000001",
            "doi": "10.0000/sample.tbi.ev",
            "title": "Intranasal extracellular vesicles for traumatic brain injury repair: a translational overview",
            "journal": "Journal of Nanobiotechnology",
            "published": "2026-05-20",
            "authors": "Sample A; Sample B",
            "abstract": "This sample article discusses intranasal mesenchymal stem cell-derived extracellular vesicles, neuroinflammation, blood-brain barrier repair and neurological recovery after traumatic brain injury.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000001/",
            "score": 88,
        },
        {
            "source": "PubMed",
            "topic": "hydrocephalus",
            "topic_cn": "脑积水与脑脊液循环",
            "id": "sample:hcp-lymph",
            "pmid": "00000002",
            "doi": "10.0000/sample.hydrocephalus",
            "title": "Meningeal lymphatic drainage and cerebrospinal fluid clearance in hydrocephalus",
            "journal": "Brain",
            "published": "2026-05-19",
            "authors": "Sample C; Sample D",
            "abstract": "This sample paper links hydrocephalus with meningeal lymphatic outflow, CSF clearance and neuroimmune remodeling.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000002/",
            "score": 84,
        },
        {
            "source": "bioRxiv",
            "topic": "microglia_trem2",
            "topic_cn": "小胶质细胞与 TREM2",
            "id": "sample:cysc-trem2",
            "pmid": "",
            "doi": "10.1101/sample.cysc.trem2",
            "title": "Cystatin C-TREM2 recognition regulates microglial uptake of extracellular vesicles",
            "journal": "bioRxiv",
            "published": "2026-05-18",
            "authors": "Sample E; Sample F",
            "abstract": "This sample preprint examines Cystatin C, CST3, TREM2 signaling and microglial endocytosis of extracellular vesicles.",
            "url": "https://doi.org/10.1101/sample.cysc.trem2",
            "score": 82,
        },
        {
            "source": "PubMed",
            "topic": "glioma_spinal",
            "topic_cn": "胶质瘤与脊髓肿瘤",
            "id": "sample:spinal-tumor",
            "pmid": "00000004",
            "doi": "10.0000/sample.spinal.tumor",
            "title": "Spatial profiling of spinal cord glioma identifies tumor-neural interface niches",
            "journal": "Acta Neuropathologica",
            "published": "2026-05-17",
            "authors": "Sample G; Sample H",
            "abstract": "This sample study uses spatial multi-omics to characterize spinal cord glioma and tumor-neural interface ecosystems.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000004/",
            "score": 80,
        },
    ]


def sample_sections() -> dict[str, list[dict]]:
    return {
        "top_journal_neuroscience": [
            {
                "source": "PubMed",
                "section": "top_journal_neuroscience",
                "section_cn": "顶刊神经科学",
                "topic": "top_journal_neuroscience",
                "topic_cn": "顶刊神经科学",
                "id": "sample:nature-neuro",
                "pmid": "00000011",
                "doi": "10.0000/sample.nature.neuro",
                "title": "A spatial atlas of human neuroinflammation identifies disease-associated microglial states",
                "journal": "Nature Neuroscience",
                "published": "2026-05-22",
                "authors": "Sample I; Sample J",
                "abstract": "This sample top-journal neuroscience paper integrates spatial transcriptomics and single-cell profiling to define microglial states across neuroinflammatory lesions.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/00000011/",
                "score": 96,
            },
            {
                "source": "PubMed",
                "section": "top_journal_neuroscience",
                "section_cn": "顶刊神经科学",
                "topic": "top_journal_neuroscience",
                "topic_cn": "顶刊神经科学",
                "id": "sample:lancet-neuro",
                "pmid": "00000012",
                "doi": "10.0000/sample.lancet.neuro",
                "title": "Shunt timing and cognitive outcomes in idiopathic normal pressure hydrocephalus: a multicentre cohort study",
                "journal": "The Lancet Neurology",
                "published": "2026-05-21",
                "authors": "Sample K; Sample L",
                "abstract": "This sample clinical cohort evaluates shunt timing, gait outcomes and cognitive trajectories in idiopathic normal pressure hydrocephalus.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/00000012/",
                "score": 94,
            },
        ],
        "global_hot_topics": [
            {
                "source": "PubMed",
                "section": "global_hot_topics",
                "section_cn": "全球学术热点",
                "topic": "global_hot_topics",
                "topic_cn": "全球学术热点",
                "id": "sample:bci",
                "pmid": "00000021",
                "doi": "10.0000/sample.bci",
                "title": "Brain-computer interface foundation models for decoding speech and movement intention",
                "journal": "Nature",
                "published": "2026-05-20",
                "authors": "Sample M; Sample N",
                "abstract": "This sample hot-topic paper describes foundation-model methods for neural decoding and discusses translational issues in brain-computer interfaces.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/00000021/",
                "score": 90,
            }
        ],
        "medical_news": [
            {
                "source": "NIH News Releases",
                "section": "medical_news",
                "section_cn": "国内外医学与医药新闻",
                "topic": "medical_news",
                "topic_cn": "国内外医学与医药新闻",
                "id": "sample:nih-news",
                "pmid": "",
                "doi": "",
                "title": "NIH launches a new initiative to accelerate neurological disease biomarker discovery",
                "journal": "NIH News Releases",
                "published": "2026-05-22",
                "authors": "",
                "abstract": "This sample news item summarizes a new biomedical funding and translational research initiative related to neurological biomarkers.",
                "url": "https://www.nih.gov/news-events/news-releases",
                "score": 70,
            }
        ],
    }


def main() -> None:
    config = yaml.safe_load((BASE_DIR / "config/topics.yaml").read_text(encoding="utf-8"))
    sections = {
        key: enrich_items(enrich_metrics_many(items))
        for key, items in sample_sections().items()
    }
    write_outputs(enrich_items(enrich_metrics_many(sample_items())), ["Preview mode: sample data only."], config, sections=sections)
    print("Preview generated: index.html, data/latest.json, output/briefing.md, output/briefing.txt")


if __name__ == "__main__":
    main()
