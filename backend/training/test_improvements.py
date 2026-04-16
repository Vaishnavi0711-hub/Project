#!/usr/bin/env python
"""
Verification script to test the improved model
Shows:
1. Consistency of predictions for same audio (should now be identical)
2. Risk scores for obvious scams (should now be higher)
3. Ensemble voting in action
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_model():
    """Test the improved CNN model."""
    
    print("\n" + "="*70)
    print("IMPROVED MODEL VERIFICATION TEST")
    print("="*70)
    
    try:
        from app.services.cnn_deepfake_detector import CNNDeepfakeDetector
        import os
        
        # Initialize detector
        model_path = Path('backend/models/cnn_deepfake_best.pt')
        detector = CNNDeepfakeDetector(
            model_path=str(model_path) if model_path.exists() else None,
            device='auto'
        )
        
        print(f"\nModel Status:")
        print(f"  Model Loaded: {detector.model_loaded}")
        print(f"  Device: {detector.device}")
        
        # Find test audio files
        genuine_dir = Path('backend/training/data/audio/genuine')
        scam_dir = Path('backend/training/data/audio/scam')
        
        test_files = {
            'Genuine Examples': list(genuine_dir.glob('*.wav'))[:2] if genuine_dir.exists() else [],
            'Scam Examples': list(scam_dir.glob('*.wav'))[:2] if scam_dir.exists() else []
        }
        
        print(f"\nFoundTest Files:")
        for category, files in test_files.items():
            print(f"  {category}: {len(files)} files")
        
        # Test consistency (same audio should give same score)
        print("\n" + "-"*70)
        print("TEST 1: PREDICTION CONSISTENCY (same audio, multiple calls)")
        print("-"*70)
        
        if test_files['Genuine Examples']:
            test_file = str(test_files['Genuine Examples'][0])
            print(f"\nTesting with: {Path(test_file).name}")
            
            predictions = []
            for i in range(3):
                result = await detector.analyze(test_file)
                risk = result['risk_score']
                prob = result['deepfake_probability']
                predictions.append(prob)
                
                print(f"  Run {i+1}: Risk={risk}%, Prob={prob:.3f}")
            
            variance = max(predictions) - min(predictions)
            print(f"\n  Variance: {variance:.3f} (should be very small for consistency)")
            if variance < 0.05:
                print(f"  ✓ PASS: Predictions are consistent")
            else:
                print(f"  ⚠ WARN: Predictions vary too much")
        
        # Test sensitivity to scams
        print("\n" + "-"*70)
        print("TEST 2: SCAM DETECTION SENSITIVITY")
        print("-"*70)
        
        if test_files['Scam Examples']:
            for test_file in test_files['Scam Examples'][:1]:
                test_file = str(test_file)
                result = await detector.analyze(test_file)
                
                print(f"\nFile: {Path(test_file).name}")
                print(f"  Risk Score: {result['risk_score']}%")
                print(f"  Probability: {result['deepfake_probability']:.3f}")
                print(f"  Confidence: {result['confidence']}")
                print(f"  Threats: {result['threat_types']}")
                print(f"  Ensemble Size: {result.get('ensemble_size', '?')}")
                print(f"  Ensemble Variance: {result.get('ensemble_variance', '?')}")
                
                if result['risk_score'] > 50:
                    print(f"  ✓ PASS: Scam properly flagged as high risk")
                else:
                    print(f"  ⚠ WARN: Scam risk score seems low")
        
        # Test genuine audio
        print("\n" + "-"*70)
        print("TEST 3: GENUINE AUDIO HANDLING")
        print("-"*70)
        
        if test_files['Genuine Examples']:
            for test_file in test_files['Genuine Examples'][:1]:
                test_file = str(test_file)
                result = await detector.analyze(test_file)
                
                print(f"\nFile: {Path(test_file).name}")
                print(f"  Risk Score: {result['risk_score']}%")
                print(f"  Probability: {result['deepfake_probability']:.3f}")
                print(f"  Confidence: {result['confidence']}")
                print(f"  Threats: {result['threat_types']}")
                
                if result['risk_score'] < 40:
                    print(f"  ✓ PASS: Genuine audio correctly identified as low risk")
                else:
                    print(f"  ⚠ WARN: Genuine audio flagged as too risky")
        
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("""
1. If tests fail, run enhanced training:
   python backend/training/quick_retrain.py

2. To improve further:
   - Collect more training data (goal: 100+ samples)
   - Use harder to distinguish scam examples
   - Retrain regularly with online learning feedback

3. Understanding the improvements:
   - Ensemble voting: 4 predictions per audio (original + 3 variations)
   - Data augmentation: Pitch shift, time stretch, noise during training
   - Stronger regularization: Prevents overfitting to small dataset
   - Conservative thresholds: Flags uncertainty as suspicious
   
4. Expected improvements:
   ✓ Consistent predictions for same audio
   ✓ Higher risk scores for obvious scams
   ✓ Better generalization to unseen audio
   ✓ Lower false negatives (fewer missed scams)
        """)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\nError: {e}")


if __name__ == '__main__':
    asyncio.run(test_model())
