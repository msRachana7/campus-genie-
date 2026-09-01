# Campus Genie refinement tasks

- [x] Make the student dashboard feel more magnetic and playful without losing usability.
- [x] Make Campus Pulse a prominent first-class mode in navigation and home discovery.
- [x] Enrich Campus Pulse with a live vibe hero, mood index, trend categories, and anonymized-signal explanation.
- [x] Add stronger visual hierarchy, motion, and campus artifact cues to the revised experience.
- [x] Verify desktop and mobile views, then save a new checkpoint for delivery.

## Vibrant campus-life update

- [x] Add motion graphics and ambient campus-life motion to the Home page.
- [x] Rework Community into a more social, poster-like, interactive experience.
- [x] Transform Campus Pulse into a vibrant youth-focused live campus visualization.
- [x] Verify reduced-motion behavior, responsive layouts, and interactions before delivery.

## Immersive backdrop and Pulse redesign

- [x] Create a persistent animated campus-life backdrop spanning the page shell and content views.
- [x] Rebuild Campus Pulse as a vibrant story-driven mode rather than a standard analytics panel.
- [x] Add a clear live campus mood map with playful signal clusters, activity constellations, and event energy.
- [x] Verify the continuous backdrop stays readable, performant, accessible, and responsive.

## Auth and profile refinement

- [x] Make login the first screen shown on initial load with name, password, forgot-password, and create-account actions.
- [x] Add an attractive create-account state within the same login experience.
- [x] Make the top-right avatar open a complete student profile view with avatar, identity, contact, academics, skills, and interests.
- [x] Remove the “Make room for affordable joy” Campus Pulse story.
- [x] Verify entry, profile, responsive behavior, and final live checkpoint.

## Routed auth update

- [x] Route Forgot Password to its own page and remove it from the login form surface.
- [x] Route New User to its own onboarding page with name, department, contact, email, skills, and interests.
- [x] Make the auth pages visually consistent and provide back-navigation between them.
- [x] Remove the entire gentle-reminder section from Campus Pulse.
- [x] Verify the auth routes, mobile layout, and final live checkpoint.

## Exact removal fix

- [x] Remove all rendered copies of the “Make room for affordable joy” Campus Pulse card.
- [x] Remove the Forgot Password action entirely from the login screen.
- [x] Verify the mobile screenshot no longer shows either unwanted element.

## Registration field refinement

- [x] Make department a dropdown with the requested BMSCE departments.
- [x] Make year of study a dropdown with years 1 through 4 and remove semester wording.
- [x] Update the profile page to show only year of study.
- [x] Validate login email addresses to allow only the bmsce.ac.in domain and show invalid username feedback.
- [x] Verify the updated forms and save a live checkpoint.

## Registration email validation

- [x] Require New User email IDs to end with @bmsce.ac.in.
- [x] Show invalid email feedback and block profile creation for non-BMSCE addresses.
- [x] Verify the registration submit behavior and save a live checkpoint.

## Multi-select registration fields

- [x] Convert Skills into a multi-select dropdown with Python, Java, HTML, CSS, and DSA.
- [x] Convert Interests into a multi-select dropdown with Hackathon, AI, ML, Technical Talks, and Research.
- [x] Verify multiple selections display correctly in the Orchard Commons form and save a live checkpoint.

## Dataset vocabulary normalization

- [x] Restrict every skills value to Python, Java, HTML, CSS, or DSA.
- [x] Restrict every interests value to Hackathon, AI, ML, Technical Talks, or Research.
- [x] Validate all 40 records and deliver the updated JSON file.

## Multiple student interests

- [x] Give every student at least two approved interests.
- [x] Validate the dataset still contains exactly 40 records and only approved interest values.
- [x] Deliver the updated JSON file.

## Sample campus posts dataset

- [x] Create 30 posts using the requested post schema.
- [x] Link post authors to existing student IDs S001–S040 and vary campus post types.
- [x] Validate JSON structure, IDs, dates, and numeric team slots.
- [x] Deliver the sample posts JSON file.

## Community reactions

- [x] Remove likes and comments display from Community posts.
- [x] Add a clickable Like / Dislike control with an active state.
- [x] Verify the Community interaction and save the live checkpoint.

## Interested-only Community action

- [x] Remove Like, Dislike, and Comment controls from Community posts.
- [x] Add one clickable Interested action with a clear selected state.
- [x] Verify only frontend files changed and save the live checkpoint.

## Student data model alignment

- [ ] Compare the 40-student dataset with the profile/onboarding fields.
- [ ] Add only missing fields such as email and contact number; preserve existing fields.
- [ ] Confirm whether persistence requires upgrading the static project to a database-backed project.
- [ ] Validate the aligned records and document the resulting data model.

## JSON profile fields

- [x] Add email and contact_number to all 40 existing student records.
- [x] Preserve all existing student fields and approved vocabularies.
- [x] Validate and deliver the updated JSON dataset for later Databricks integration.

## Community post schema alignment

- [x] Add initials, color, name, meta, body, and tags to the 30-post dataset.
- [x] Preserve post_id, author_id, type, title, skills_required, deadline, and team_slots.
- [x] Do not add likes or comments; keep the Interested-only interaction model.
- [x] Validate and deliver the aligned posts JSON file.

## Clean posts dataset fields

- [x] Remove only `color` and `name` from the aligned posts dataset.
- [x] Preserve all remaining post fields and validate 30 records.
- [x] Deliver the cleaned JSON file.

## Community deadline display

- [x] Add a formatted deadline label to each Community post card.
- [x] Preserve the existing Interested-only action and JSON dataset.
- [x] Verify the updated frontend and save a live checkpoint.

## BMSCE club recruitment dataset

- [x] Review the provided BMSCE Extra-Curricular Activities page and identify club names.
- [x] Create exactly 25 recruitment-only posts in the existing post schema.
- [x] Validate that every record is recruitment-related and the JSON structure is correct.
- [x] Deliver the new recruitment posts JSON file.

## Technical event promotion dataset

- [x] Create exactly 30 event-promotion posts in the aligned schema.
- [x] Restrict event topics to hackathons, tech talks, workshops, conferences, coding sprints, and developer meetups.
- [x] Validate that every record is an opportunity/event promotion and has valid dates and team slots.
- [x] Deliver the technical events JSON file.

## Event dates in body copy

- [x] Add the event date explicitly to every technical event post body.
- [x] Preserve the existing deadline field and all other post fields.
- [x] Validate all 30 bodies and deliver the updated JSON file.

## Skill-based opportunity dataset

- [x] Create exactly 30 opportunity posts requesting specific skills for defined work.
- [x] Use the aligned post schema and approved student skill vocabulary.
- [x] Validate that every body describes a concrete task and every skills_required array is non-empty.
- [x] Deliver the skill-based opportunity JSON file.

## Research paper collaboration dataset

- [x] Create exactly 30 posts seeking people or teammates for research papers.
- [x] Cover varied technical research topics and concrete collaboration roles.
- [x] Use the aligned post schema with non-empty skills_required and valid deadlines.
- [x] Validate and deliver the research collaboration JSON file.

## Resources filter repair

- [x] Make filter options visible when the Resources filter is opened.
- [x] Make filter selection update the notes/PYQs list.
- [x] Verify the filter interaction and save a live checkpoint.

## Resources year filter

- [x] Replace the Semester filter label and state with Year of study.
- [x] Add working Year 1, Year 2, Year 3, and Year 4 options and update resource data.
- [x] Verify the filter behavior and save a live checkpoint.

## Full frontend QA pass

- [x] Audit every top-level view and visible interaction for dead controls, missing states, and formatting issues.
- [x] Check login, registration, profile, Resources, Community, Ask Genie, Campus Pulse, and Time Capsule flows.
- [x] Fix the Community/forum sidebar so it participates correctly in page scrolling.
- [x] Run type/build checks and inspect frontend console/network errors.
- [x] Verify desktop and mobile behavior, then save a live checkpoint.

## Vercel access troubleshooting

- [ ] Confirm the Vercel account matches the GitHub repository owner.
- [ ] Ensure the Vercel GitHub app has access to the Campus Genie repository.
- [ ] Retry repository import and document the next step or error screenshot needed.

## Cross-tab UI refinements

- [x] Keep the Community green banner stationary while only its text loops right-to-left.
- [x] Add a working Share action to each Community post.
- [x] Remove the calendar icon from deadline rows.
- [x] Ensure skill-request posts expose the requested skills as specification tags.
- [x] Move the Ask Genie profile control from bottom-left to a top position.
- [x] Keep the left navigation rail stationary across every tab while page content scrolls.
- [x] Replace the specific “before the DS quiz” copy with generic Notes/PYQs wording.
- [x] Verify all affected views and save a live checkpoint.

## Create a Post composer

- [x] Add a dedicated Create a Post page accessible from Community.
- [x] Collect post type, title, body, skills required, deadline, team slots, and tags.
- [x] Keep the form frontend-only with validation, cancel/back navigation, and success feedback.
- [x] Verify the composer on desktop/mobile and save a live checkpoint.

## Campus Pulse interaction routing

- [x] Route every clickable Pulse signal, post/story card, and action to the Community page.
- [x] Preserve the Pulse visuals while making the destination behavior consistent.

## Resource shelf and Community cleanup

- [x] Remove the Community “Your Match Map” / connect-with-people panel.
- [x] Add an explicit Create a Post action inside the Community filters as well as the hero action.
- [x] Add a dedicated resource-upload page collecting type, title, subject, year, file, description, page count, and tags.
- [x] Add the generated generic study visual to the Notes/PYQs feature panel.
