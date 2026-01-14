"""Phase 1 Pydantic Configuration Verification Test"""
import sys
sys.path.insert(0, r'c:\Users\User\Documents\docling\docling\kaggle\implementation_folder')

from config.settings import ConversionConfig, GradientConfig, GPUConfig, LangChainConfig, OCRConfig

config = ConversionConfig()

# Expected values
expected = {
    'gradient.enabled': True,
    'enhance_tables': True,
    'enhance_text': True,
    'gpu.device': 'cuda',
    'gpu.num_gpus': 2,
    'gpu.enable_parallel': True,
    'gpu.ocr_batch_size': 32,
    'gpu.layout_batch_size': 64,
    'gpu.table_batch_size': 4,
    'langchain.enabled': True,
}

# Actual values
actual = {
    'gradient.enabled': config.gradient.enabled,
    'enhance_tables': config.enhance_tables,
    'enhance_text': config.enhance_text,
    'gpu.device': config.gpu.device,
    'gpu.num_gpus': config.gpu.num_gpus,
    'gpu.enable_parallel': config.gpu.enable_parallel,
    'gpu.ocr_batch_size': config.gpu.ocr_batch_size,
    'gpu.layout_batch_size': config.gpu.layout_batch_size,
    'gpu.table_batch_size': config.gpu.table_batch_size,
    'langchain.enabled': config.langchain.enabled,
}

# Compare and report
print("=" * 60)
print("Phase 1 Pydantic Configuration Verification")
print("=" * 60)
print()

all_passed = True
for key in expected:
    exp_val = expected[key]
    act_val = actual[key]
    passed = exp_val == act_val
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{key:30} = {str(act_val):10} (expected: {str(exp_val):10}) {status}")
    if not passed:
        all_passed = False

print()
print("=" * 60)
if all_passed:
    print("OVERALL STATUS: ✅ ALL TESTS PASSED")
else:
    print("OVERALL STATUS: ❌ SOME TESTS FAILED")
print("=" * 60)
