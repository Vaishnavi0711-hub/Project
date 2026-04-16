"""
Example script demonstrating CNN deepfake detector inference

This shows how to:
1. Load a trained CNN model
2. Analyze audio files
3. Display results
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.cnn_deepfake_detector import CNNDeepfakeDetector
from app.services.deepfake_detector import DeepfakeDetector

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def analyze_audio_cnn(audio_path: str):
    """
    Analyze audio using CNN detector.
    
    Args:
        audio_path: Path to audio file
    """
    
    print("\n" + "="*60)
    print("CNN Deepfake Detection")
    print("="*60)
    
    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"❌ Error: Audio file not found: {audio_path}")
        return
    
    print(f"📁 File: {audio_file.name}")
    print(f"📏 Size: {audio_file.stat().st_size / 1024:.1f} KB")
    
    # Initialize detector
    model_path = Path(__file__).parent.parent / 'models' / 'cnn_deepfake_best.pt'
    detector = CNNDeepfakeDetector(
        model_path=str(model_path) if model_path.exists() else None,
        device='auto'
    )
    
    print(f"🧠 Model loaded: {detector.model_loaded}")
    print(f"📱 Device: {detector.device}")
    
    # Analyze
    print("\n🔍 Analyzing audio...")
    result = await detector.analyze(str(audio_file))
    
    # Display results
    print("\n" + "-"*60)
    print("RESULTS")
    print("-"*60)
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Deepfake Probability: {result.get('deepfake_probability', 'N/A')}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model Type: {result['model_type']}")
    print(f"Threat Types: {', '.join(result['threat_types']) if result['threat_types'] else 'None detected'}")
    print(f"\nExplanation:\n{result['explanation']}")
    print("-"*60)
    
    # Risk level indicator
    score = result['risk_score']
    if score >= 80:
        risk_emoji = "🔴"
        risk_level = "CRITICAL"
    elif score >= 60:
        risk_emoji = "🟠"
        risk_level = "MEDIUM"
    elif score >= 40:
        risk_emoji = "🟡"
        risk_level = "LOW"
    else:
        risk_emoji = "🟢"
        risk_level = "VERY LOW"
    
    print(f"\n{risk_emoji} Risk Level: {risk_level}")
    print("="*60 + "\n")


async def compare_detectors(audio_path: str):
    """
    Compare CNN and heuristic detectors on the same audio.
    
    Args:
        audio_path: Path to audio file
    """
    
    print("\n" + "="*60)
    print("Comparing CNN vs Heuristic Detectors")
    print("="*60)
    
    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"❌ Error: Audio file not found: {audio_path}")
        return
    
    print(f"📁 File: {audio_file.name}\n")
    
    # CNN Detector
    model_path = Path(__file__).parent.parent / 'models' / 'cnn_deepfake_best.pt'
    cnn_detector = CNNDeepfakeDetector(
        model_path=str(model_path) if model_path.exists() else None,
        device='auto'
    )
    
    print("🧠 CNN Detector")
    print(f"   Model loaded: {cnn_detector.model_loaded}")
    print(f"   Device: {cnn_detector.device}")
    cnn_result = await cnn_detector.analyze(str(audio_file))
    print(f"   Risk Score: {cnn_result['risk_score']}/100")
    print(f"   Confidence: {cnn_result['confidence']}\n")
    
    # Heuristic Detector
    heuristic_detector = DeepfakeDetector()
    print("📊 Heuristic Detector")
    heuristic_result = await heuristic_detector.analyze(str(audio_file))
    print(f"   Risk Score: {heuristic_result['risk_score']}/100")
    print(f"   Confidence: {heuristic_result['confidence']}\n")
    
    # Comparison
    diff = abs(cnn_result['risk_score'] - heuristic_result['risk_score'])
    print("-"*60)
    print(f"Difference: {diff}/100")
    
    if cnn_result['risk_score'] > heuristic_result['risk_score']:
        print(f"CNN is {diff}% more cautious")
    elif cnn_result['risk_score'] < heuristic_result['risk_score']:
        print(f"Heuristic is {diff}% more cautious")
    else:
        print("Both detectors agree")
    print("="*60 + "\n")


def batch_analyze(audio_dir: str):
    """
    Analyze all audio files in a directory.
    
    Args:
        audio_dir: Directory containing audio files
    """
    
    audio_path = Path(audio_dir)
    if not audio_path.is_dir():
        print(f"❌ Error: Directory not found: {audio_dir}")
        return
    
    audio_files = list(audio_path.glob('**/*.wav'))
    audio_files += list(audio_path.glob('**/*.mp3'))
    
    if not audio_files:
        print(f"❌ No audio files found in {audio_dir}")
        return
    
    print(f"\n📁 Found {len(audio_files)} audio files\n")
    
    # Initialize detector once
    model_path = Path(__file__).parent.parent / 'models' / 'cnn_deepfake_best.pt'
    detector = CNNDeepfakeDetector(
        model_path=str(model_path) if model_path.exists() else None,
        device='auto'
    )
    
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Analyzing {audio_file.name}...", end='', flush=True)
        
        try:
            # Run async in a new event loop for each file
            result = asyncio.run(detector.analyze(str(audio_file)))
            results.append({
                'file': audio_file.name,
                'risk_score': result['risk_score'],
                'threat_types': result['threat_types'],
                'confidence': result['confidence']
            })
            print(f" ✓ Risk: {result['risk_score']}/100")
        except Exception as e:
            print(f" ❌ Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("BATCH ANALYSIS SUMMARY")
    print("="*60)
    
    if results:
        high_risk = [r for r in results if r['risk_score'] >= 70]
        medium_risk = [r for r in results if 40 <= r['risk_score'] < 70]
        low_risk = [r for r in results if r['risk_score'] < 40]
        
        print(f"High Risk (70+): {len(high_risk)}")
        print(f"Medium Risk (40-69): {len(medium_risk)}")
        print(f"Low Risk (<40): {len(low_risk)}")
        print(f"\nAverage Risk Score: {sum(r['risk_score'] for r in results) / len(results):.1f}/100")
        
        if high_risk:
            print(f"\n🔴 High Risk Files:")
            for r in high_risk:
                print(f"   - {r['file']}: {r['risk_score']}/100")
    
    print("="*60 + "\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CNN Deepfake Detection Examples')
    parser.add_argument(
        'command',
        choices=['analyze', 'compare', 'batch'],
        help='Command to run'
    )
    parser.add_argument(
        'audio',
        help='Path to audio file or directory'
    )
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        print("\n🎤 Analyzing single audio file...")
        asyncio.run(analyze_audio_cnn(args.audio))
    
    elif args.command == 'compare':
        print("\n⚖️ Comparing detectors...")
        asyncio.run(compare_detectors(args.audio))
    
    elif args.command == 'batch':
        print("\n📂 Batch analyzing directory...")
        batch_analyze(args.audio)


"""
USAGE EXAMPLES:

1. Analyze a single audio file:
   python inference_example.py analyze path/to/audio.wav

2. Compare CNN vs Heuristic detectors:
   python inference_example.py compare path/to/audio.wav

3. Analyze all audio files in a directory:
   python inference_example.py batch path/to/audio_folder/

4. From Python:
   from backend.training.inference_example import analyze_audio_cnn
   await analyze_audio_cnn('audio.wav')
"""
