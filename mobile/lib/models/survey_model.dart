import 'dart:convert';

class Survey {
  final String id;
  final String title;
  final List<Question> questions;
  final String? description;
  
  Survey({
    required this.id,
    required this.title,
    required this.questions,
    this.description,
  });
  
  factory Survey.fromJson(Map<String, dynamic> json) {
    return Survey(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'],
      questions: (json['questions'] as List? ?? [])
          .map((q) => Question.fromJson(q))
          .toList(),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'questions': questions.map((q) => q.toJson()).toList(),
    };
  }
}

class Question {
  final String id;
  final String type;
  final String text;
  final bool required;
  final List<String>? retryPrompts;
  final Map<String, dynamic>? extractConfig;
  
  Question({
    required this.id,
    required this.type,
    required this.text,
    this.required = true,
    this.retryPrompts,
    this.extractConfig,
  });
  
  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json['id'] ?? '',
      type: json['type'] ?? 'text',
      text: json['text'] ?? '',
      required: json['required'] ?? true,
      retryPrompts: (json['retry_prompts'] as List?)?.cast<String>(),
      extractConfig: json['extract_config'] as Map<String, dynamic>?,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'text': text,
      'required': required,
      'retry_prompts': retryPrompts,
      'extract_config': extractConfig,
    };
  }
}

class SurveyResponse {
  final String id;
  final String surveyId;
  final String? respondentId;
  final Map<String, dynamic> responses;
  final DateTime createdAt;
  final bool synced;
  final LocationData? location;
  final Map<String, dynamic>? deviceInfo;
  final Map<String, double>? confidenceScores;
  final bool isComplete;

  SurveyResponse({
    required this.id,
    required this.surveyId,
    this.respondentId,
    required this.responses,
    required this.createdAt,
    required this.synced,
    this.location,
    this.deviceInfo,
    this.confidenceScores,
    this.isComplete = false,
  });

  factory SurveyResponse.fromMap(Map<String, dynamic> map) {
    return SurveyResponse(
      id: map['id'] ?? '',
      surveyId: map['survey_id'] ?? '',
      respondentId: map['respondent_id'],
      responses: map['responses'] is String ? 
        jsonDecode(map['responses']) : map['responses'] ?? {},
      createdAt: DateTime.parse(map['created_at'] ?? DateTime.now().toIso8601String()),
      synced: (map['synced'] ?? 0) == 1,
      location: (map['location_lat'] != null && map['location_lng'] != null) ? 
        LocationData(
          latitude: map['location_lat']?.toDouble() ?? 0.0,
          longitude: map['location_lng']?.toDouble() ?? 0.0,
        ) : null,
      deviceInfo: map['device_info'] is String ? 
        jsonDecode(map['device_info']) : map['device_info'],
      confidenceScores: map['confidence_scores'] is String ?
        Map<String, double>.from(jsonDecode(map['confidence_scores']) ?? {}) :
        Map<String, double>.from(map['confidence_scores'] ?? {}),
      isComplete: (map['is_complete'] ?? 0) == 1,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'survey_id': surveyId,
      'respondent_id': respondentId,
      'responses': jsonEncode(responses),
      'created_at': createdAt.toIso8601String(),
      'synced': synced ? 1 : 0,
      'location_lat': location?.latitude,
      'location_lng': location?.longitude,
      'device_info': deviceInfo != null ? jsonEncode(deviceInfo) : null,
      'confidence_scores': confidenceScores != null ? jsonEncode(confidenceScores) : null,
      'is_complete': isComplete ? 1 : 0,
    };
  }
}

class LocationData {
  final double latitude;
  final double longitude;

  LocationData({
    required this.latitude,
    required this.longitude,
  });

  Map<String, dynamic> toMap() {
    return {
      'latitude': latitude,
      'longitude': longitude,
    };
  }
}
