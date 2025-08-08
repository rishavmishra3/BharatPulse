import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:camera/camera.dart';
import '../models/survey_model.dart';
import '../widgets/voice_recorder.dart';
import '../widgets/progress_indicator.dart';
import '../services/storage_service.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
final String baseUrl = 'http://192.168.1.120:8000/api'

class SurveyScreen extends StatefulWidget {
  @override
  _SurveyScreenState createState() => _SurveyScreenState();
}

class _SurveyScreenState extends State<SurveyScreen> {
  late stt.SpeechToText _speech;
  late FlutterTts _tts;
  
  Survey? currentSurvey;
  int currentQuestionIndex = 0;
  bool _isListening = false;
  bool _isSpeaking = false;
  String _currentText = '';
  double _confidence = 0.0;
  
  Map<String, dynamic> responses = {};
  StorageService _storageService = StorageService();
  
  @override
  void initState() {
    super.initState();
    _initializeSpeech();
    _initializeTTS();
    _loadSurvey();
  }
  
  void _initializeSpeech() async {
    _speech = stt.SpeechToText();
    bool available = await _speech.initialize(
      onStatus: (status) => print('Speech status: $status'),
      onError: (error) => print('Speech error: $error'),
    );
    
    if (!available) {
      _showError('Speech recognition not available');
    }
  }
  
  void _initializeTTS() async {
    _tts = FlutterTts();
    
    // Configure TTS for Hindi
    await _tts.setLanguage('hi-IN');
    await _tts.setSpeechRate(0.4); // Slower for better comprehension
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);
    
    _tts.setCompletionHandler(() {
      setState(() {
        _isSpeaking = false;
      });
    });
  }
  
  void _loadSurvey() {
    // Load survey definition from assets or API
    setState(() {
      currentSurvey = Survey(
        id: "rural_livelihood_2024",
        title: "ग्रामीण आजीविका सर्वेक्षण",
        questions: [
          Question(
            id: "intro",
            type: "audio_only",
            text: "नमस्ते! मैं आपकी आजीविका के बारे में कुछ सवाल पूछना चाहता हूँ।",
          ),
          Question(
            id: "consent",
            type: "yes_no",
            text: "क्या आप इस सर्वेक्षण में भाग लेना चाहते हैं?",
            required: true,
          ),
          Question(
            id: "name",
            type: "text_extract",
            text: "आपका नाम क्या है?",
            required: true,
          ),
          Question(
            id: "age",
            type: "number_extract",
            text: "आपकी उम्र कितनी है?",
            required: true,
          ),
          Question(
            id: "location",
            type: "text_extract",
            text: "आप कहाँ रहते हैं?",
            required: true,
          ),
          Question(
            id: "occupation",
            type: "text_extract",
            text: "आप क्या काम करते हैं?",
            required: true,
          ),
          Question(
            id: "income",
            type: "number_extract",
            text: "आपकी महीने की कमाई कितनी है?",
            required: false,
          ),
        ],
      );
    });
    
    // Speak the introduction
    _speakQuestion();
  }
  
  void _startListening() async {
    if (!_isListening && !_isSpeaking) {
      bool available = await _speech.initialize();
      if (available) {
        setState(() => _isListening = true);
        _speech.listen(
          onResult: (result) {
            setState(() {
              _currentText = result.recognizedWords;
              _confidence = result.confidence;
            });
          },
          listenFor: Duration(seconds: 30),
          pauseFor: Duration(seconds: 3),
          partialResults: true,
          localeId: 'hi-IN', // Hindi locale
        );
      }
    }
  }
  
  void _stopListening() async {
    if (_isListening) {
      await _speech.stop();
      setState(() => _isListening = false);
      
      // Process the response
      if (_currentText.isNotEmpty && _confidence > 0.5) {
        _processResponse(_currentText);
      } else {
        _showRetryDialog();
      }
    }
  }
  
  void _speakQuestion() async {
    if (currentSurvey != null && 
        currentQuestionIndex < currentSurvey!.questions.length) {
      
      setState(() => _isSpeaking = true);
      
      Question question = currentSurvey!.questions[currentQuestionIndex];
      await _tts.speak(question.text);
    }
  }
  
  void _processResponse(String response) async {
    if (currentSurvey == null) return;
    
    Question currentQuestion = currentSurvey!.questions[currentQuestionIndex];
    
    // Send to backend for NLP processing
    try {
      Map<String, dynamic> processed = await _callNLPService(
        response, 
        currentQuestion.id
      );
      
      if (processed['confidence'] > 0.7) {
        // Accept the response
        responses[currentQuestion.id] = processed['extracted_data'];
        _moveToNextQuestion();
      } else {
        // Ask for clarification
        _askForClarification();
      }
      
    } catch (e) {
      _showError('Processing failed: $e');
    }
  }
  
  void _moveToNextQuestion() {
    if (currentSurvey != null && 
        currentQuestionIndex < currentSurvey!.questions.length - 1) {
      
      setState(() {
        currentQuestionIndex++;
        _currentText = '';
        _confidence = 0.0;
      });
      
      // Speak next question after a brief pause
      Future.delayed(Duration(seconds: 1), () {
        _speakQuestion();
      });
      
    } else {
      _completeSurvey();
    }
  }
  
  void _completeSurvey() async {
    // Save responses to local database
    SurveyResponse response = SurveyResponse(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      surveyId: currentSurvey!.id,
      responses: responses,
      createdAt: DateTime.now(),
      synced: false,
    );
    
    await _storageService.saveResponse(response);
    
    // Show completion message
    await _tts.speak('धन्यवाद! आपका सर्वेक्षण पूरा हो गया।');
    
    // Navigate back or show summary
    Navigator.of(context).pop();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.green.shade50,
      appBar: AppBar(
        title: Text('BharatPulse', style: TextStyle(fontSize: 24)),
        backgroundColor: Colors.green,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.sync),
            onPressed: _syncData,
          ),
        ],
      ),
      body: Column(
        children: [
          // Progress indicator
          if (currentSurvey != null)
            CustomProgressIndicator(
              current: currentQuestionIndex + 1,
              total: currentSurvey!.questions.length,
            ),
          
          Expanded(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Question text
                  if (currentSurvey != null && 
                      currentQuestionIndex < currentSurvey!.questions.length)
                    Container(
                      padding: EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.grey.withOpacity(0.1),
                            spreadRadius: 2,
                            blurRadius: 8,
                          ),
                        ],
                      ),
                      child: Text(
                        currentSurvey!.questions[currentQuestionIndex].text,
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w500,
                          height: 1.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  
                  SizedBox(height: 40),
                  
                  // Voice recorder
                  VoiceRecorder(
                    isListening: _isListening,
                    onStartListening: _startListening,
                    onStopListening: _stopListening,
                    currentText: _currentText,
                    confidence: _confidence,
                  ),
                  
                  SizedBox(height: 24),
                  
                  // Utility buttons
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      ElevatedButton.icon(
                        onPressed: _isSpeaking ? null : _speakQuestion,
                        icon: Icon(Icons.replay),
                        label: Text('दोबारा सुनें'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          padding: EdgeInsets.symmetric(
                            horizontal: 20, 
                            vertical: 12
                          ),
                        ),
                      ),
                      
                      ElevatedButton.icon(
                        onPressed: _moveToNextQuestion,
                        icon: Icon(Icons.skip_next),
                        label: Text('छोड़ें'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange,
                          padding: EdgeInsets.symmetric(
                            horizontal: 20, 
                            vertical: 12
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Future<Map<String, dynamic>> _callNLPService(String text, String questionId) async {
    try {
      // Call your FastAPI backend
      final response = await http.post(
        Uri.parse('http://your-api-url.com/api/process-voice'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'text': text,
          'question_id': questionId,
          'user_lang': 'hi',
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('API call failed');
      }
    } catch (e) {
      // Return mock data for development
      return {
        'extracted_data': {'response': text},
        'confidence': 0.8,
        'success': true,
      };
    }
  }
  
  void _syncData() async {
    try {
      // Get unsynced responses
      List<SurveyResponse> unsyncedResponses = await _storageService.getUnsyncedResponses();
      
      if (unsyncedResponses.isEmpty) {
        _showMessage('सभी डेटा सिंक हो चुका है');
        return;
      }
      
      // Show syncing dialog
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          content: Row(
            children: [
              CircularProgressIndicator(),
              SizedBox(width: 20),
              Text('डेटा सिंक हो रहा है...'),
            ],
          ),
        ),
      );
      
      // Sync each response
      for (SurveyResponse response in unsyncedResponses) {
        await _syncSingleResponse(response);
      }
      
      Navigator.pop(context); // Close syncing dialog
      _showMessage('${unsyncedResponses.length} रिस्पांस सिंक हो गए');
      
    } catch (e) {
      Navigator.pop(context); // Close syncing dialog
      _showError('सिंक में समस्या: $e');
    }
  }
  
  Future<void> _syncSingleResponse(SurveyResponse response) async {
    try {
      final httpResponse = await http.post(
        Uri.parse('http://your-api-url.com/api/surveys/${response.surveyId}/responses'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'id': response.id,
          'survey_id': response.surveyId,
          'responses': response.responses,
          'created_at': response.createdAt.toIso8601String(),
        }),
      );
      
      if (httpResponse.statusCode == 200 || httpResponse.statusCode == 201) {
        await _storageService.markSynced(response.id);
      }
    } catch (e) {
      print('Error syncing response ${response.id}: $e');
    }
  }
  
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, style: TextStyle(fontSize: 16)),
        backgroundColor: Colors.red,
        duration: Duration(seconds: 3),
      ),
    );
  }
  
  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, style: TextStyle(fontSize: 16)),
        backgroundColor: Colors.green,
        duration: Duration(seconds: 2),
      ),
    );
  }
  
  void _showRetryDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('स्पष्ट नहीं सुना'),
        content: Text('कृपया दोबारा बोलिए, धीरे और स्पष्ट आवाज में'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _startListening();
            },
            child: Text('फिर से कोशिश करें'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _moveToNextQuestion();
            },
            child: Text('छोड़ें'),
          ),
        ],
      ),
    );
  }
  
  void _askForClarification() async {
    await _tts.speak('मुझे पूरी तरह समझ नहीं आया। कृपया दोबारा बताएं।');
    _startListening();
  }
}
