import 'package:flutter/material.dart';

class VoiceRecorder extends StatelessWidget {
  final bool isListening;
  final VoidCallback onStartListening;
  final VoidCallback onStopListening;
  final String currentText;
  final double confidence;
  
  const VoiceRecorder({
    Key? key,
    required this.isListening,
    required this.onStartListening,
    required this.onStopListening,
    required this.currentText,
    required this.confidence,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Voice visualization
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isListening ? Colors.red.shade100 : Colors.green.shade100,
            border: Border.all(
              color: isListening ? Colors.red : Colors.green,
              width: 3,
            ),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: isListening ? onStopListening : onStartListening,
              borderRadius: BorderRadius.circular(60),
              child: Icon(
                isListening ? Icons.mic : Icons.mic_none,
                size: 50,
                color: isListening ? Colors.red : Colors.green,
              ),
            ),
          ),
        ),
        
        SizedBox(height: 16),
        
        // Status text
        Text(
          isListening ? 'सुन रहा हूँ...' : 'बोलने के लिए माइक दबाएं',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.grey.shade600,
          ),
        ),
        
        SizedBox(height: 16),
        
        // Current text display
        if (currentText.isNotEmpty)
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.blue.shade200),
            ),
            child: Column(
              children: [
                Text(
                  currentText,
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.blue.shade800,
                  ),
                  textAlign: TextAlign.center,
                ),
                
                SizedBox(height: 8),
                
                // Confidence indicator
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('विश्वसनीयता: '),
                    Container(
                      width: 100,
                      height: 8,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(4),
                        color: Colors.grey.shade300,
                      ),
                      child: FractionallySizedBox(
                        widthFactor: confidence,
                        alignment: Alignment.centerLeft,
                        child: Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(4),
                            color: confidence > 0.7 
                              ? Colors.green 
                              : confidence > 0.5 
                                ? Colors.orange 
                                : Colors.red,
                          ),
                        ),
                      ),
                    ),
                    SizedBox(width: 8),
                    Text('${(confidence * 100).toInt()}%'),
                  ],
                ),
              ],
            ),
          ),
      ],
    );
  }
}
