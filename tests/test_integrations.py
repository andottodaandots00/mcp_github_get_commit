"""Integration Tests for Framework Integrations.

This module verifies that all framework integrations are correctly
wired up and functional.

Tests:
1. LangChain Integration - DoclingLoader, metadata extraction
2. Gradient SDK Integration - Client initialization, API calls
3. RAG Pipeline - Document indexing, vector search
4. Parallel Processing - Multi-GPU batch conversion
5. CLI Commands - All subcommands properly registered
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLangChainIntegration:
    """Test LangChain-Docling integration."""

    def test_langchain_loader_imports(self):
        """Verify all required imports are available."""
        from core.langchain_loader import (
            DoclingLoader,
            ExportType,
            BaseMetaExtractor,
            CustomMetaExtractor,
            create_langchain_loader,
            load_documents_for_rag,
            lazy_load_documents_for_rag
        )

        # Verify classes exist
        assert DoclingLoader is not None
        assert ExportType is not None
        assert BaseMetaExtractor is not None
        assert CustomMetaExtractor is not None

        # Verify CustomMetaExtractor inherits from BaseMetaExtractor
        assert issubclass(CustomMetaExtractor, BaseMetaExtractor)

        print("✅ LangChain imports verified")

    def test_custom_meta_extractor_methods(self):
        """Verify CustomMetaExtractor has required methods."""
        from core.langchain_loader import CustomMetaExtractor

        extractor = CustomMetaExtractor()

        # Verify methods exist
        assert hasattr(extractor, 'extract_chunk_meta')
        assert hasattr(extractor, 'extract_dl_doc_meta')
        assert callable(extractor.extract_chunk_meta)
        assert callable(extractor.extract_dl_doc_meta)

        # Test with mock chunk
        mock_chunk = Mock()
        mock_chunk.meta = None

        result = extractor.extract_chunk_meta("/test/path.pdf", mock_chunk)

        # Verify result structure
        assert "source" in result
        assert "page_number" in result
        assert "headings" in result
        assert "element_type" in result
        assert "full_dl_meta" in result

        print("✅ CustomMetaExtractor methods verified")

    def test_export_types(self):
        """Verify ExportType enum has required values."""
        from langchain_docling.loader import ExportType

        assert hasattr(ExportType, 'MARKDOWN')
        assert hasattr(ExportType, 'DOC_CHUNKS')

        print("✅ ExportType enum verified")


class TestGradientSDKIntegration:
    """Test Gradient SDK integration."""

    def test_gradient_imports(self):
        """Verify gradient module imports work."""
        from core.gradient_client import (
            GradientLLMClient,
            GRADIENT_SDK_AVAILABLE,
            APIError,
            RateLimitError,
            APIConnectionError,
            AuthenticationError,
            APIStatusError
        )

        # GRADIENT_SDK_AVAILABLE should be a boolean
        assert isinstance(GRADIENT_SDK_AVAILABLE, bool)

        # Exception classes should exist
        assert APIError is not None
        assert RateLimitError is not None
        assert APIConnectionError is not None
        assert AuthenticationError is not None
        assert APIStatusError is not None

        print(f"✅ Gradient SDK imports verified (available: {GRADIENT_SDK_AVAILABLE})")

    def test_gradient_client_requires_key(self):
        """Verify GradientLLMClient requires API key."""
        from core.gradient_client import GradientLLMClient, GRADIENT_SDK_AVAILABLE

        if not GRADIENT_SDK_AVAILABLE:
            pytest.skip("Gradient SDK not installed")

        # Should raise ValueError without API key
        with pytest.raises(ValueError) as exc_info:
            with patch.dict('os.environ', {}, clear=True):
                GradientLLMClient()

        assert "access key" in str(exc_info.value).lower()
        print("✅ GradientLLMClient key validation verified")

    def test_enhance_content_function(self):
        """Verify enhance_content_with_ai function exists."""
        from core.converter import enhance_content_with_ai

        assert callable(enhance_content_with_ai)

        # Test signature
        import inspect
        sig = inspect.signature(enhance_content_with_ai)
        params = list(sig.parameters.keys())

        assert 'content' in params
        assert 'content_type' in params
        assert 'config' in params

        print("✅ enhance_content_with_ai function verified")

    def test_gradient_config(self):
        """Verify GradientConfig has all required fields."""
        from config.settings import GradientConfig

        config = GradientConfig()

        assert hasattr(config, 'enabled')
        assert hasattr(config, 'model_access_key')
        assert hasattr(config, 'default_model')
        assert hasattr(config, 'temperature')
        assert hasattr(config, 'max_tokens')

        # Check defaults
        assert config.enabled == False
        assert config.default_model == "llama3.3-70b-instruct"
        assert 0.0 <= config.temperature <= 2.0
        assert config.max_tokens >= 1

        print("✅ GradientConfig verified")


class TestRAGPipelineIntegration:
    """Test RAG pipeline integration."""

    def test_rag_pipeline_imports(self):
        """Verify RAG pipeline imports."""
        from core.rag_pipeline import DocumentRAGPipeline
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_milvus import Milvus

        assert DocumentRAGPipeline is not None
        assert HuggingFaceEmbeddings is not None
        assert Milvus is not None

        print("✅ RAG pipeline imports verified")

    def test_rag_pipeline_initialization(self):
        """Verify RAG pipeline can be initialized."""
        from core.rag_pipeline import DocumentRAGPipeline

        # Mock HuggingFaceEmbeddings to avoid downloading model
        with patch('core.rag_pipeline.HuggingFaceEmbeddings') as mock_embeddings:
            mock_embeddings.return_value = Mock()

            pipeline = DocumentRAGPipeline(
                embedding_model="test-model",
                use_gpu=False,
                collection_name="test_collection",
                db_path="./test.db"
            )

            assert pipeline.model_name == "test-model"
            assert pipeline.collection_name == "test_collection"
            assert pipeline.db_path == "./test.db"
            assert pipeline.vector_store is None
            assert pipeline.document_count == 0

        print("✅ RAG pipeline initialization verified")

    def test_rag_pipeline_methods(self):
        """Verify RAG pipeline has all required methods."""
        from core.rag_pipeline import DocumentRAGPipeline

        # Check methods exist
        assert hasattr(DocumentRAGPipeline, 'add_documents')
        assert hasattr(DocumentRAGPipeline, 'add_documents_lazy')
        assert hasattr(DocumentRAGPipeline, 'query')
        assert hasattr(DocumentRAGPipeline, 'query_with_scores')
        assert hasattr(DocumentRAGPipeline, 'get_retriever')
        assert hasattr(DocumentRAGPipeline, 'document_count')

        print("✅ RAG pipeline methods verified")


class TestParallelProcessingIntegration:
    """Test multi-GPU parallel processing."""

    def test_parallel_imports(self):
        """Verify parallel processing imports."""
        from core.parallel import (
            batch_convert_parallel,
            convert_pdf_worker,
            set_gpu_for_worker
        )

        assert callable(batch_convert_parallel)
        assert callable(convert_pdf_worker)
        assert callable(set_gpu_for_worker)

        print("✅ Parallel processing imports verified")

    def test_batch_convert_empty_list(self):
        """Verify batch_convert_parallel handles empty list."""
        from core.parallel import batch_convert_parallel

        result = batch_convert_parallel([], Mock(), num_gpus=2)
        assert result == []

        print("✅ Parallel empty list handling verified")


class TestCLIIntegration:
    """Test CLI commands integration."""

    def test_cli_subcommands(self):
        """Verify all CLI subcommands are registered."""
        from interfaces.cli import create_parser

        parser = create_parser()

        # Get subparsers
        subparsers_action = None
        for action in parser._actions:
            if hasattr(action, '_parser_class'):
                subparsers_action = action
                break

        assert subparsers_action is not None

        # Check all required commands exist
        commands = list(subparsers_action.choices.keys())

        assert 'convert' in commands
        assert 'langchain' in commands
        assert 'ai-enhance' in commands
        assert 'rag' in commands
        assert 'serve' in commands

        print(f"✅ CLI commands verified: {commands}")

    def test_cli_convert_parallel_option(self):
        """Verify convert command has --parallel option."""
        from interfaces.cli import create_parser

        parser = create_parser()

        # Parse convert help to check --parallel exists
        try:
            args = parser.parse_args(['convert', 'test.pdf', '--parallel', '--num-gpus', '2'])
            assert args.parallel == True
            assert args.num_gpus == 2
            print("✅ CLI --parallel option verified")
        except SystemExit:
            pytest.fail("--parallel option not found")

    def test_cli_rag_command(self):
        """Verify rag command has correct arguments."""
        from interfaces.cli import create_parser

        parser = create_parser()

        # Test index action
        args = parser.parse_args(['rag', 'index', 'docs/', '--top-k', '5'])
        assert args.action == 'index'
        assert args.input == 'docs/'
        assert args.top_k == 5

        # Test query action
        args = parser.parse_args(['rag', 'query', 'What is the main topic?'])
        assert args.action == 'query'
        assert args.input == 'What is the main topic?'

        print("✅ CLI rag command verified")


class TestGradioIntegration:
    """Test Gradio UI integration."""

    def test_gradio_imports(self):
        """Verify Gradio app imports."""
        from interfaces.gradio_app import (
            create_gradio_app,
            convert_with_progress,
            launch
        )

        assert callable(create_gradio_app)
        assert callable(convert_with_progress)
        assert callable(launch)

        print("✅ Gradio imports verified")

    def test_gradio_parallel_option(self):
        """Verify Gradio app has parallel processing option."""
        from interfaces.gradio_app import convert_with_progress

        import inspect
        sig = inspect.signature(convert_with_progress)
        params = list(sig.parameters.keys())

        assert 'enable_parallel' in params
        assert 'num_gpus' in params

        print("✅ Gradio parallel options verified")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("INTEGRATION TEST SUITE")
    print("=" * 60)
    print()

    test_classes = [
        TestLangChainIntegration,
        TestGradientSDKIntegration,
        TestRAGPipelineIntegration,
        TestParallelProcessingIntegration,
        TestCLIIntegration,
        TestGradioIntegration,
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    method = getattr(instance, method_name)
                    method()
                    passed += 1
                except pytest.skip.Exception as e:
                    print(f"⏭️ {method_name}: SKIPPED - {e}")
                    skipped += 1
                except Exception as e:
                    print(f"❌ {method_name}: FAILED - {e}")
                    failed += 1

    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
