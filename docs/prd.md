# The Photo Archivist Product Requirements Document (PRD)

## Goals and Background Context

### Goals
- Enable users to efficiently identify and manage duplicate and similar images within directory structures
- Provide an intuitive macOS-native interface for reviewing and selecting images for archival
- Reduce storage waste by helping users remove redundant image files
- Maintain user control over which images to keep vs. archive with intelligent pre-selection
- Deliver a fast, reliable scanning experience that handles large image collections

### Background Context
Many users accumulate thousands of photos across various folders, often containing duplicates from multiple imports, similar shots from burst mode, or near-identical images with slight variations. Manually identifying these duplicates is time-consuming and error-prone. The Photo Archivist addresses this pain point by leveraging advanced image analysis to detect both exact and visually similar duplicates, presenting them in an organized interface that allows users to make informed decisions about which images to preserve in their active collection versus archive for potential future reference.

### Change Log
| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2024-12-20 | 1.0 | Initial PRD creation | Product Owner |

## Requirements

### Functional Requirements

1. **FR1**: The application shall provide a folder selection interface allowing users to choose a single root directory for scanning
2. **FR2**: The application shall recursively traverse the selected directory and all subdirectories to identify image files in common formats (.jpg, .jpeg, .png, .gif)
3. **FR3**: The application shall use the imagededup library to detect both exact duplicates (using PHash/DHash) and visually similar images using CNN analysis
4. **FR4**: The application shall provide a configurable similarity threshold via slider control ranging from "Strict" to "Loose" matching
5. **FR5**: The application shall display a progress bar during the scanning operation with meaningful status updates
6. **FR6**: The application shall group detected duplicates and similar images together in the results interface
7. **FR7**: The application shall display thumbnail previews of grouped images side-by-side for easy comparison
8. **FR8**: The application shall show file name and full path information for each image thumbnail
9. **FR9**: The application shall provide individual checkboxes for each image to enable user selection for archival
10. **FR10**: The application shall automatically pre-select lower-quality or smaller-sized images in each group while allowing user override
11. **FR11**: The application shall create an "Archived" folder in the user's home directory if it doesn't exist
12. **FR12**: The application shall move selected images to the Archived folder maintaining original filenames
13. **FR13**: The application shall place all archived images directly in the Archived folder without replicating original directory structure
14. **FR14**: The application shall display confirmation messages upon successful completion of archival operations
15. **FR15**: The application shall handle file access errors and missing files gracefully with user-friendly error messages

### Non-Functional Requirements

1. **NFR1**: The application shall be optimized for macOS with native look and feel using PyQt/PySide
2. **NFR2**: The scanning operation shall handle collections of up to 10,000 images without performance degradation
3. **NFR3**: The thumbnail generation shall be responsive with lazy loading for large result sets
4. **NFR4**: The application shall use efficient memory management to prevent crashes during large scans
5. **NFR5**: The similarity detection accuracy shall be configurable to balance speed vs. precision
6. **NFR6**: The user interface shall remain responsive during scanning operations through proper threading
7. **NFR7**: The application shall preserve file metadata and timestamps during move operations

## User Interface Design Goals

### Overall UX Vision
The Photo Archivist should feel like a native macOS application with clean, intuitive design that makes the complex task of duplicate management feel simple and efficient. The interface should guide users through a clear workflow: select → scan → review → archive, with each step feeling natural and providing appropriate feedback.

### Key Interaction Paradigms
- **File system integration**: Native folder picker and drag-drop support
- **Visual comparison**: Side-by-side thumbnail layout for easy duplicate assessment  
- **Batch operations**: Checkbox-based selection with smart defaults and bulk actions
- **Progressive disclosure**: Start simple, reveal advanced options (similarity threshold) as needed
- **Non-destructive workflow**: Archive rather than delete, with clear messaging about what's happening

### Core Screens and Views
1. **Main Application Window**: Central hub with folder selection, scan controls, and results area
2. **Folder Selection Dialog**: Native macOS folder picker interface
3. **Scanning Progress View**: Progress bar with status updates and cancel option
4. **Results Review Interface**: Grouped thumbnails with selection controls and image details
5. **Settings/Preferences Panel**: Similarity threshold and archive location configuration
6. **Confirmation Dialogs**: Archive operation confirmation and completion status

### Accessibility: WCAG AA
The application will support standard macOS accessibility features including VoiceOver compatibility, keyboard navigation, and appropriate contrast ratios.

### Branding
Clean, modern design following macOS Human Interface Guidelines with subtle use of color to indicate groupings and selections. Professional appearance suitable for both casual users and photography professionals.

### Target Device and Platforms: Desktop Only
Designed specifically for macOS desktop environment, optimized for mouse and keyboard interaction with support for trackpad gestures where appropriate.

## Technical Assumptions

### Repository Structure: Monorepo
Single repository containing the complete Python application with all dependencies and resources.

### Service Architecture
Desktop application architecture with modular design separating image processing, UI components, and file management into distinct modules for maintainability and testing.

### Testing Requirements
Unit testing for core image processing logic, integration testing for file operations, and manual testing protocols for UI workflows. Automated testing for critical paths like duplicate detection accuracy and file handling edge cases.

### Additional Technical Assumptions and Requests
- **Python 3.9+**: Modern Python version with good library support
- **imagededup library**: Primary dependency for duplicate detection capabilities
- **PyQt6/PySide6**: For native macOS GUI development with modern widget support
- **Threading**: Background processing for scanning to maintain UI responsiveness  
- **Error handling**: Comprehensive exception handling for file system operations
- **Logging**: Detailed logging for debugging and user support
- **Packaging**: Application bundling for easy distribution (e.g., py2app for macOS .app bundle)

## Epic List

### Epic 1: Foundation & Core Infrastructure
Establish project setup, basic application structure, and fundamental image scanning capabilities with a simple working interface.

### Epic 2: Duplicate Detection & Analysis
Implement sophisticated duplicate detection using imagededup with configurable similarity thresholds and efficient processing of large image collections.

### Epic 3: User Interface & Review Workflow  
Create comprehensive UI for reviewing detected duplicates with thumbnail display, grouping, selection controls, and user-friendly comparison tools.

### Epic 4: Archive Management & File Operations
Implement secure file archival system with error handling, user confirmations, and proper file management including the creation and organization of archived images.

## Epic 1: Foundation & Core Infrastructure

**Epic Goal**: Establish a working macOS desktop application with basic folder selection, image file discovery, and simple duplicate detection to validate the core technical approach and provide a foundation for advanced features.

### Story 1.1: Project Setup and Application Bootstrap
As a developer,
I want to set up the basic Python project structure with PyQt/PySide,
so that I have a working foundation for building the Photo Archivist application.

#### Acceptance Criteria
1. Python project is initialized with proper virtual environment and dependency management
2. PyQt6 or PySide6 is installed and basic window displays successfully
3. Project structure includes separate modules for UI, image processing, and file operations
4. Basic logging configuration is implemented
5. Application can be launched and displays a simple main window
6. Unit testing framework is configured and basic tests pass

### Story 1.2: Basic Folder Selection Interface
As a user,
I want to select a folder to scan for images,
so that I can specify which directory contains the photos I want to analyze.

#### Acceptance Criteria  
1. Main window includes a "Choose Folder" button that opens native macOS folder picker
2. Selected folder path is displayed in a text field
3. Only directories can be selected (files are filtered out)
4. Selected path is validated to ensure it exists and is readable
5. Error message is shown if selected folder cannot be accessed
6. Folder selection state is maintained during the application session

### Story 1.3: Image File Discovery and Listing
As a user,
I want the application to find all image files in my selected folder and subfolders,
so that I can see what images will be analyzed for duplicates.

#### Acceptance Criteria
1. Application recursively scans selected directory for image files (.jpg, .jpeg, .png, .gif)
2. File discovery respects common image file extensions (case insensitive)
3. Hidden files and system directories are appropriately handled/skipped
4. Total count of discovered images is displayed to user
5. Basic error handling for permission issues or corrupted directory structures
6. Scan operation can be cancelled by user if needed
7. Progress indication is shown during file discovery process

### Story 1.4: Basic Duplicate Detection Implementation
As a user,
I want to see a simple list of duplicate images found in my folder,
so that I can verify the core duplicate detection functionality is working.

#### Acceptance Criteria
1. imagededup library is integrated and functional
2. Basic hash-based duplicate detection (PHash or DHash) is implemented
3. Detected duplicates are grouped and displayed in a simple list format
4. Each duplicate group shows file paths of matching images
5. Basic error handling for corrupted or unreadable image files
6. Detection process shows progress indication
7. Results clearly indicate how many duplicate groups were found
8. Simple "Scan for Duplicates" button triggers the detection process

## Epic 2: Duplicate Detection & Analysis

**Epic Goal**: Implement sophisticated duplicate and similar image detection with configurable similarity thresholds, CNN-based analysis for near-duplicates, and optimized performance for large image collections.

### Story 2.1: Advanced Similarity Detection with CNN
As a user,
I want to detect visually similar images (not just exact duplicates),
so that I can find near-duplicate photos that might have slight differences in quality or editing.

#### Acceptance Criteria
1. CNN-based similarity detection is implemented using imagededup's CNN features
2. Both exact duplicates (hash-based) and similar images (CNN-based) are detected in single scan
3. Similar image groups are clearly distinguished from exact duplicate groups in results
4. CNN model loading and initialization is handled efficiently
5. Memory usage is optimized for CNN operations on large image sets
6. Error handling for CNN model loading failures or insufficient system resources
7. Progress indication shows both hash and CNN processing phases

### Story 2.2: Configurable Similarity Threshold
As a user,
I want to adjust how strict the similarity matching is,
so that I can control whether to find only very similar images or include more loosely related ones.

#### Acceptance Criteria
1. Slider control is added to UI with range from "Strict" to "Loose" similarity matching
2. Slider position maps to appropriate threshold values for imagededup CNN analysis
3. Threshold changes trigger re-analysis of already processed images (if applicable)
4. Default threshold is set to a reasonable middle value for most users
5. Threshold setting is persisted between application sessions
6. Visual feedback shows approximate impact of threshold changes
7. Tooltip or help text explains what strict vs loose matching means

### Story 2.3: Performance Optimization for Large Collections
As a user,
I want the scanning process to handle thousands of images efficiently,
so that I can process large photo collections without excessive wait times or memory issues.

#### Acceptance Criteria
1. Image processing is batched to manage memory usage effectively
2. Progress bar shows meaningful progress through large collections
3. Scanning can handle at least 5,000 images without crashing or excessive slowdown
4. Memory usage remains reasonable (under 2GB) even with large collections
5. CPU utilization is optimized to use available cores efficiently
6. Temporary files or caches are cleaned up properly after processing
7. User can cancel long-running operations gracefully
8. Performance metrics are logged for debugging and optimization

### Story 2.4: Enhanced Progress Reporting and Cancellation
As a user,
I want detailed progress information during scanning and the ability to cancel long operations,
so that I stay informed and maintain control over the process.

#### Acceptance Criteria
1. Progress bar shows percentage completion with estimated time remaining
2. Current processing phase is clearly indicated (file discovery, hashing, CNN analysis, etc.)
3. Current file being processed is optionally displayed
4. Cancel button remains responsive during all processing phases
5. Cancellation cleanly stops processing and returns to ready state
6. Partial results are preserved if user cancels after some processing
7. Progress information is updated at reasonable intervals (not too frequent to impact performance)
8. Memory and resources are properly cleaned up on cancellation

## Epic 3: User Interface & Review Workflow

**Epic Goal**: Create an intuitive and comprehensive user interface for reviewing detected duplicates with thumbnail displays, intelligent grouping, selection controls, and easy comparison tools that enable users to make informed decisions about which images to archive.

### Story 3.1: Thumbnail Display and Image Grouping
As a user,
I want to see thumbnail previews of duplicate and similar images grouped together,
so that I can visually compare them and decide which ones to keep or archive.

#### Acceptance Criteria
1. Detected duplicate/similar groups are displayed with thumbnail previews of each image
2. Thumbnails are generated efficiently and cached for performance
3. Images within each group are displayed side-by-side for easy comparison
4. Group headers clearly indicate the type of match (exact duplicate vs similar)
5. Thumbnail size is appropriate for comparison while fitting multiple images on screen
6. Lazy loading is implemented for large result sets to maintain responsiveness
7. Image loading errors are handled gracefully with placeholder thumbnails
8. Groups can be expanded/collapsed for better navigation

### Story 3.2: Image Information and Metadata Display
As a user,
I want to see file names, paths, and basic information for each image,
so that I can identify images and understand their context before making archival decisions.

#### Acceptance Criteria
1. Each thumbnail displays the filename below or overlaid on the image
2. Full file path is shown either persistently or on hover/selection
3. Basic file information is displayed (file size, dimensions, date modified)
4. File information is formatted clearly and consistently
5. Long file paths are truncated appropriately with tooltips showing full path
6. File size is displayed in human-readable format (KB, MB, etc.)
7. Image dimensions are shown in standard format (width x height pixels)
8. Information display doesn't interfere with thumbnail comparison workflow

### Story 3.3: Individual Image Selection Controls
As a user,
I want to select specific images within each group for archival using checkboxes,
so that I have precise control over which images are moved to the archive folder.

#### Acceptance Criteria
1. Each image thumbnail has an associated checkbox for selection
2. Checkboxes are clearly visible and easy to interact with
3. Selected images are visually indicated (highlight, border, or overlay)
4. Selection state is maintained as user navigates through results
5. Individual selection changes update any group-level selection indicators
6. Checkbox interactions don't interfere with image viewing or comparison
7. Selection state is preserved if user returns to previous groups
8. Clear visual distinction between selected and unselected images

### Story 3.4: Intelligent Pre-selection of Lower Quality Images
As a user,
I want the application to automatically pre-select lower quality or smaller images in each group,
so that I have a good starting point for selection while retaining the ability to override these choices.

#### Acceptance Criteria
1. Algorithm automatically analyzes images in each group for quality factors (resolution, file size)
2. Lower quality images are pre-selected by default in each duplicate group
3. Pre-selection logic considers multiple factors: resolution, file size, image sharpness (if feasible)
4. User can easily override pre-selections by clicking checkboxes
5. Pre-selection algorithm is conservative (prefers to pre-select fewer images when uncertain)
6. Visual indication shows which images were pre-selected vs manually selected
7. User can disable auto-selection feature if desired
8. Pre-selection rationale is available (e.g., "smaller file size" tooltip)

### Story 3.5: Batch Selection and Group Management
As a user,
I want to select entire groups or use batch selection operations,
so that I can efficiently manage large numbers of duplicates without individual clicking.

#### Acceptance Criteria
1. Each duplicate group has a group-level checkbox to select/deselect all images in that group
2. "Select All" and "Deselect All" buttons are available for all results
3. Group selection respects individual overrides (partial selection state indicated)
4. Batch operations update individual checkboxes appropriately
5. Selection counts are displayed (e.g., "15 of 47 images selected")
6. Keyboard shortcuts support common selection operations
7. Group selection state is visually clear (checked, unchecked, or indeterminate)
8. Batch selection operations are performant even with large result sets

## Epic 4: Archive Management & File Operations

**Epic Goal**: Implement a secure and reliable file archival system that moves selected images to a designated archive folder with proper error handling, user confirmations, and comprehensive file management including progress tracking and rollback capabilities.

### Story 4.1: Archive Folder Creation and Management
As a user,
I want the application to create and manage an archive folder for storing duplicate images,
so that archived images are organized in a predictable location separate from my active photo collection.

#### Acceptance Criteria
1. "Archived" folder is created in the user's home directory if it doesn't exist
2. Archive folder location is configurable in application settings
3. Folder creation handles permission issues gracefully with clear error messages
4. Archive folder path is validated and displayed to user before operations
5. Application checks available disk space before archival operations
6. Archive folder structure is documented and consistent
7. User can browse to archive folder location from within the application
8. Archive folder creation respects macOS security and permission requirements

### Story 4.2: Secure File Move Operations
As a user,
I want selected images to be safely moved to the archive folder with proper error handling,
so that my files are relocated without data loss or corruption.

#### Acceptance Criteria
1. Selected images are moved (not copied) to the archive folder to free up space
2. Original filenames are preserved in the archive folder
3. File conflicts are handled appropriately (rename with suffix if needed)
4. File permissions and timestamps are preserved during move operations
5. Move operations are atomic where possible to prevent partial failures
6. Detailed error handling for permission issues, disk full, and file locks
7. Failed move operations don't leave files in inconsistent state
8. Move operations maintain file integrity (checksums verified if feasible)

### Story 4.3: Archive Operation Progress and Confirmation
As a user,
I want to see progress during archival operations and receive confirmation when complete,
so that I understand what's happening and know when the operation has finished successfully.

#### Acceptance Criteria
1. Progress bar shows archival operation progress with file count information
2. Current file being moved is optionally displayed during operation
3. Archive operation can be cancelled with graceful cleanup of partial operations
4. Success confirmation dialog shows number of files moved and archive folder location
5. Error summary is provided if some files couldn't be moved
6. Operation log is available showing which files were moved and any issues encountered
7. Progress indication is accurate and updates at reasonable intervals
8. Confirmation includes option to open archive folder in Finder

### Story 4.4: Error Handling and Recovery
As a user,
I want clear information about any problems during archival operations and options for recovery,
so that I can understand what went wrong and take appropriate action.

#### Acceptance Criteria
1. Specific error messages for common issues (permissions, disk space, file locks)
2. List of files that couldn't be moved with specific reasons for each failure
3. Option to retry failed operations after user addresses underlying issues
4. Partial success scenarios are handled gracefully (some files moved, others failed)
5. Error messages include suggested solutions where applicable
6. Critical errors don't crash the application or leave files in bad state
7. Error details are logged for troubleshooting and support
8. User can continue using application normally after handling errors

### Story 4.5: Archive Operation Summary and Cleanup
As a user,
I want a comprehensive summary of archival operations and automatic cleanup of the interface,
so that I can see what was accomplished and continue with additional scans if needed.

#### Acceptance Criteria
1. Final summary shows total files archived, any errors, and time taken
2. Successfully archived images are removed from the duplicate results display
3. Remaining unarchived duplicates stay visible for potential future action
4. Archive summary includes disk space freed up by the operation
5. Option to immediately scan for additional duplicates in the same or different folder
6. Interface returns to ready state for new operations
7. Archive history is optionally maintained for user reference
8. Summary can be saved or exported for record-keeping if desired

## Next Steps

### UX Expert Prompt
@ux-expert Please create detailed UI/UX specifications and wireframes for The Photo Archivist macOS desktop application based on this PRD. Focus on:

**Core Interface Design:**
- Native macOS window layout with proper toolbar and sidebar integration
- Folder selection interface with drag-drop support and breadcrumb navigation
- Configurable similarity threshold slider with visual feedback
- Progress indicators for scanning operations with cancel functionality

**Duplicate Review Workflow:**
- Thumbnail grid layout optimized for side-by-side image comparison
- Visual grouping of duplicate/similar images with clear group headers
- Checkbox selection system with intelligent pre-selection highlighting
- Image metadata overlay (filename, size, dimensions) with hover states
- Batch selection controls and group management interface

**Key UX Requirements:**
- Maintain macOS Human Interface Guidelines compliance
- Ensure WCAG AA accessibility standards
- Design for mouse, keyboard, and trackpad interaction patterns
- Create responsive layouts that handle 100+ duplicate groups efficiently
- Implement clear visual hierarchy and information architecture

Please deliver wireframes, interaction flows, and detailed component specifications that development teams can implement directly.

### Architect Prompt  
@architect Please create a comprehensive technical architecture for The Photo Archivist Python desktop application based on this PRD. Design for:

**Core Architecture:**
- Python 3.9+ application structure with PyQt6/PySide6 for macOS native GUI
- Modular design separating UI, image processing, and file management concerns
- Threading architecture for background processing while maintaining UI responsiveness
- Memory management strategies for handling large image collections (5000+ files)

**Key Technical Integration:**
- imagededup library integration for both hash-based and CNN-based duplicate detection
- Efficient thumbnail generation and caching system
- File system operations with proper error handling and atomic move operations
- Configuration management for user preferences and similarity thresholds

**Performance & Reliability:**
- Batch processing strategies for large image collections
- Progress tracking and cancellation mechanisms
- Comprehensive error handling for file permissions, disk space, and corrupted files
- Logging and debugging infrastructure

**Deployment Considerations:**
- macOS application bundling (py2app) for distribution
- Dependency management and virtual environment setup
- Testing strategy covering unit tests, integration tests, and UI automation

Please deliver detailed architecture diagrams, class structures, and implementation guidelines that align with the 20 user stories defined in this PRD.
