"""
Test script for online learning system
Verifies all components work correctly
"""

import asyncio
import tempfile
import numpy as np
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Would need to be run with proper imports available


async def test_secure_deletion():
    """Test secure file deletion."""
    from app.services.online_learning import SecureDeletion
    
    logger.info("Testing secure deletion...")
    
    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
        f.write(b"test data" * 1000)
    
    # Verify it exists
    assert Path(temp_path).exists(), "Temp file not created"
    
    # Delete securely
    result = await SecureDeletion.secure_delete(temp_path, verify=True)
    
    assert result, "Deletion failed"
    assert not Path(temp_path).exists(), "File still exists after deletion"
    
    logger.info("✓ Secure deletion works")


async def test_ewc():
    """Test Elastic Weight Consolidation."""
    from app.models.cnn_model import DeepfakeCNN
    from app.services.online_learning import ElasticWeightConsolidation
    import torch
    
    logger.info("Testing EWC...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepfakeCNN().to(device)
    
    # Create EWC wrapper
    ewc = ElasticWeightConsolidation(model, lambda_ewc=0.1)
    
    # Verify attributes
    assert ewc.model is not None, "Model not assigned"
    assert ewc.lambda_ewc == 0.1, "Lambda not set"
    assert ewc.fisher_information is None, "Should be None initially"
    
    logger.info("✓ EWC initialization works")


async def test_online_learning_init():
    """Test online learning service initialization."""
    from app.services.online_learning import OnlineLearningService, OnlineLearningConfig
    from app.models.cnn_model import DeepfakeCNN
    import torch
    
    logger.info("Testing online learning initialization...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepfakeCNN().to(device)
    
    config = OnlineLearningConfig(
        learning_rate=1e-5,
        batch_size=4,
        ewc_lambda=0.1
    )
    
    service = OnlineLearningService(
        model=model,
        model_path='models/test.pt',
        config=config
    )
    
    # Verify initialization
    assert service.model is not None, "Model not assigned"
    assert service.device == device, "Device mismatch"
    assert len(service.feedback_buffer) == 0, "Buffer should be empty"
    assert service.model_version == 0, "Version should start at 0"
    
    logger.info("✓ Online learning service initializes")


async def test_should_learn():
    """Test confidence-based sampling logic."""
    from app.services.online_learning import OnlineLearningService, OnlineLearningConfig
    from app.models.cnn_model import DeepfakeCNN
    import torch
    
    logger.info("Testing confidence-based sampling...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepfakeCNN().to(device)
    
    service = OnlineLearningService(
        model=model,
        config=OnlineLearningConfig(confidence_threshold=0.70)
    )
    
    # Case 1: Model right and confident -> skip
    should_learn = service._should_learn(
        user_label=1,
        model_label=1,
        model_confidence=0.95
    )
    assert not should_learn, "Should skip when confident and correct"
    
    # Case 2: Model wrong -> learn
    should_learn = service._should_learn(
        user_label=1,
        model_label=0,
        model_confidence=0.60
    )
    assert should_learn, "Should learn when model is wrong"
    
    # Case 3: Model right but not confident -> learn (potentially)
    should_learn = service._should_learn(
        user_label=1,
        model_label=1,
        model_confidence=0.55
    )
    assert should_learn, "Should learn when not confident"
    
    logger.info("✓ Confidence-based sampling works correctly")


async def test_feature_extraction():
    """Test mel-spectrogram feature extraction."""
    from app.services.online_learning import OnlineLearningService, OnlineLearningConfig
    from app.models.cnn_model import DeepfakeCNN
    import torch
    import librosa
    
    logger.info("Testing feature extraction...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepfakeCNN().to(device)
    
    service = OnlineLearningService(model=model)
    
    # Create synthetic audio
    sr = 16000
    duration = 2
    t = np.linspace(0, duration, sr * duration)
    audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz sine wave
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
        import soundfile as sf
        sf.write(temp_path, audio, sr)
    
    try:
        # Extract features
        features = service._extract_features(temp_path)
        
        assert features is not None, "Features should not be None"
        assert features.shape[0] == 1, "Should have 1 channel"
        assert features.shape[1] == 128, "Should have 128 mel bins"
        assert features.dim() == 3, "Should be 3D tensor (C, H, W)"
        
        logger.info(f"✓ Feature extraction works (shape: {features.shape})")
        
    finally:
        # Cleanup
        Path(temp_path).unlink()


async def test_configuration():
    """Test configuration system."""
    from app.services.online_learning import OnlineLearningConfig
    
    logger.info("Testing configuration...")
    
    # Default config
    config1 = OnlineLearningConfig()
    assert config1.learning_rate == 1e-5, "Default LR should be 1e-5"
    assert config1.batch_size == 4, "Default batch size should be 4"
    
    # Custom config
    config2 = OnlineLearningConfig(
        learning_rate=1e-4,
        batch_size=8,
        ewc_lambda=0.5
    )
    assert config2.learning_rate == 1e-4, "Custom LR not set"
    assert config2.batch_size == 8, "Custom batch size not set"
    assert config2.ewc_lambda == 0.5, "Custom EWC lambda not set"
    
    logger.info("✓ Configuration system works")


async def run_all_tests():
    """Run all tests."""
    
    logger.info("=" * 60)
    logger.info("ONLINE LEARNING SYSTEM - TEST SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("Secure Deletion", test_secure_deletion),
        ("EWC Initialization", test_ewc),
        ("Online Learning Init", test_online_learning_init),
        ("Confidence Sampling", test_should_learn),
        ("Configuration", test_configuration),
    ]
    
    # Skip feature extraction if librosa not available
    try:
        import librosa
        tests.append(("Feature Extraction", test_feature_extraction))
    except ImportError:
        logger.warning("⚠ librosa not available - skipping feature extraction test")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n[TEST] {test_name}")
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED: {e}", exc_info=True)
            failed += 1
        except SystemExit:
            logger.warning(f"⊘ {test_name} SKIPPED")
            skipped += 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Passed:  {passed}")
    logger.info(f"Failed:  {failed}")
    logger.info(f"Skipped: {skipped}")
    
    if failed == 0:
        logger.info("\n✓ ALL TESTS PASSED - System ready to use!")
    else:
        logger.error(f"\n✗ {failed} test(s) failed - Check logs above")
    
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


"""
USAGE:

Run from backend/ directory:

    python -m pytest training/test_online_learning.py -v

Or directly:

    python training/test_online_learning.py
"""
